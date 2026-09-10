# hp - fzf-powered herdr workspace launcher
#
# Usage: hp
#   Select a directory via fzf (from ghq + zoxide) and a layout, then
#   create (or join) a herdr workspace with that layout applied.

hp() {
  # herdr サーバが起動していなければ何も作らない
  # 注: `herdr status server` は起動有無によらず常に exit 0 を返す（実測確認済み）ため、
  # --json の .running で判定する。
  herdr status server --json 2>/dev/null | jq -e '.running' >/dev/null 2>&1 \
    || { echo "herdr server is not running"; return 1 }

  # ① ディレクトリ選択
  local dir
  dir=$({
    ghq list --full-path
    zoxide query -l
  } | sort -u | fzf --prompt='directory> ')
  [[ -z "$dir" ]] && return 0

  # ② layout 選択
  local layouts layout_file layout_name selected
  layouts=( ~/.config/herdr/layouts/*.json(N) )

  if (( ${#layouts} == 0 )); then
    echo "No herdr layouts found in ~/.config/herdr/layouts/"
    return 1
  elif (( ${#layouts} == 1 )); then
    layout_file="${layouts[1]}"
  else
    selected=$(printf '%s\n' "${layouts[@]:t}" | fzf --prompt='layout> ')
    [[ -z "$selected" ]] && return 0
    layout_file="$HOME/.config/herdr/layouts/${selected}"
  fi
  layout_name="${layout_file:t:r}"

  # ③ workspace 名
  local default_name="${dir:t}"
  local ws_name
  read "ws_name?Workspace name [${default_name}]: " || return 0
  ws_name="${ws_name:-$default_name}"

  # ④ 同名 workspace があれば作らずに合流する（拒否ではなく focus。AC-10）
  local existing_id
  existing_id=$(herdr workspace list | jq -r --arg label "$ws_name" '
    [.result.workspaces[] | select(.label == $label)] | sort_by(.number) | .[0].workspace_id // empty
  ')
  if [[ -n "$existing_id" ]]; then
    herdr workspace focus "$existing_id" >/dev/null
    return 0
  fi

  # ⑤ workspace 新規作成
  local create_resp tab_id
  create_resp=$(herdr workspace create --cwd "$dir" --label "$ws_name" --focus)
  if [[ $? -ne 0 ]]; then
    echo "failed to create herdr workspace"
    return 1
  fi
  tab_id=$(jq -r '.result.tab.tab_id' <<< "$create_resp")
  if [[ -z "$tab_id" || "$tab_id" == "null" ]]; then
    echo "failed to create herdr workspace"
    return 1
  fi

  # layout.apply は指定した tab_id の tab を丸ごと破棄して新しい tab / pane を
  # 作るため、初期ペイン（root_pane）の後始末は不要（K4 実測）。

  # ⑥ layout の全 pane 葉に cwd を注入して apply
  local root_json apply_params apply_resp
  root_json=$(jq --arg cwd "$dir" '
    def inject:
      if .type == "pane" then . + {cwd: $cwd}
      else (.first |= inject) | (.second |= inject)
      end;
    inject
  ' "$layout_file")
  apply_params=$(jq -n --argjson root "$root_json" --arg tab_id "$tab_id" \
    '{root: $root, tab_id: $tab_id, focus: true}')
  apply_resp=$(herdr-api layout.apply "$apply_params")
  if [[ $? -ne 0 ]]; then
    echo "failed to apply herdr layout"
    return 1
  fi

  # ⑦ dev レイアウトのときは nvim ペインへフォーカスを戻す
  #   （herdr pane focus は --direction 必須の方向移動なので使えず、
  #    絶対フォーカスは herdr-api の pane.focus を使う。apply 応答側の
  #    新規採番された pane_id を使うこと。入力に渡した ID は使い回さない）
  if [[ "$layout_name" == "dev" ]]; then
    local nvim_pane_id
    nvim_pane_id=$(jq -r '
      def find_label($l):
        if .type == "pane" then (if .label == $l then .pane_id else empty end)
        else (.first | find_label($l)), (.second | find_label($l))
        end;
      .layout.root | find_label("nvim")
    ' <<< "$apply_resp")
    [[ -n "$nvim_pane_id" ]] && herdr-api pane.focus "$(jq -n --arg pane_id "$nvim_pane_id" '{pane_id: $pane_id}')" >/dev/null
  fi
}

# hclean - 使い終わった herdr workspace を棚卸しして閉じる
#
# Usage: hclean [--age N]
#   生成 AI も走行プロセスも無い workspace を候補にし、未コミット・未 push を
#   抱えたものや新しすぎるものには WARN を付ける。判定は herdr-audit に任せ、
#   ここは fzf での選択と close だけを持つ。既定の絞り込みは status=ok。
hclean() {
  herdr status server --json 2>/dev/null | jq -e '.running' >/dev/null 2>&1 \
    || { echo "herdr server is not running"; return 1 }

  local age=3
  while (( $# )); do
    case "$1" in
      --age)   age="$2"; shift 2 ;;
      --age=*) age="${1#--age=}"; shift ;;
      -h|--help)
        echo "usage: hclean [--age N]  # N 日以上経過した空 workspace を ok と見なす (既定 3)"
        return 0 ;;
      *) echo "hclean: unknown option: $1"; return 1 ;;
    esac
  done

  local rows
  rows=$(herdr-audit --age "$age") || return 1
  [[ -z "$rows" ]] && { echo "no workspaces"; return 0 }

  # column -t 整形後は $2 = workspace_id、$NF = cwd。fzf の既定クエリ `^ok` は
  # 行頭アンカー付きの exact match で、閉じてよい workspace だけを残す。
  local selected
  selected=$(print -r -- "$rows" \
    | column -t -s $'\t' \
    | fzf --multi --query='^ok' \
          --header='TAB=選択 / ok=閉じてよい park=退避済み WARN=要確認 busy=稼働中 (クエリを消せば全件)' \
          --preview='echo {}; echo; git -C {-1} status -sb 2>/dev/null | head -20' \
          --preview-window=down,40%)
  [[ -z "$selected" ]] && return 0

  # 自分がいる workspace は選ばれていても閉じない（足元を消さないため）。表示中の
  # workspace と、hclean を打っている pane の workspace は別のことがあるので両方見る。
  local focused_id
  focused_id=$(herdr workspace list | jq -r '.result.workspaces[] | select(.focused) | .workspace_id')

  local -a ids
  ids=( ${(f)"$(print -r -- "$selected" | awk '{print $2}')"} )

  print -r -- "$selected"
  echo
  local answer
  read "answer?上記 ${#ids} 個の workspace を閉じます。よろしいですか [y/N]: " || return 0
  [[ "$answer" != [yY] ]] && { echo "中止しました"; return 0 }

  local id
  for id in "${ids[@]}"; do
    if [[ "$id" == "$focused_id" || "$id" == "${HERDR_WORKSPACE_ID:-}" ]]; then
      echo "skipped $id (自分がいる workspace)"
      continue
    fi
    if herdr workspace close "$id" >/dev/null 2>&1; then
      echo "closed  $id"
    else
      echo "failed  $id"
    fi
  done
}

# hunpark - park した herdr workspace を再開する
#
# Usage: hunpark
#   ~/.claude/data/parked/*.json を fzf で選び、workspace を作り直して各 pane で
#   `claude --resume` / `codex resume` を起動する。park レコードは park skill が
#   書く（待ち条件・外部影響・pane ごとの session id）。
hunpark() {
  herdr status server --json 2>/dev/null | jq -e '.running' >/dev/null 2>&1 \
    || { echo "herdr server is not running"; return 1 }

  local dir="$HOME/.claude/data/parked"
  local -a records
  records=( $dir/*.json(N) )
  if (( ${#records} == 0 )); then
    echo "park された workspace はありません ($dir)"
    return 0
  fi

  local selected
  selected=$(for f in "${records[@]}"; do
      jq -r --arg f "$f" '[(.parked_at // "-"), (.label // "-"), (.wait_for // "-"), $f] | @tsv' "$f"
    done | sort -r | column -t -s $'\t' \
    | fzf --expect=ctrl-x \
          --header='Enter=再開 / Ctrl-X=このレコードを捨てる (preview = park メモ)' \
          --preview='f={-1}; cat "${f%.json}.md" 2>/dev/null || cat "$f"' \
          --preview-window=down,60%)
  [[ -z "$selected" ]] && return 0

  # --expect があるので 1 行目は押されたキー（Enter なら空行）、2 行目が選択行。
  local key row
  key=${selected%%$'\n'*}
  row=${selected#*$'\n'}
  [[ -z "$row" ]] && return 0

  local record label cwd
  record=$(awk '{print $NF}' <<< "$row")

  # 戻らないと決めた park はここで捨てる（放っておくと workspace と同じように溜まる）。
  if [[ "$key" == "ctrl-x" ]]; then
    local drop
    read "drop?$(jq -r '.label // "?"' "$record") の park レコードを削除します。よろしいですか [y/N]: " || return 0
    [[ "$drop" != [yY] ]] && { echo "中止しました"; return 0 }
    rm -f "$record" "${record%.json}.md"
    echo "deleted: ${record:t}"
    return 0
  fi
  label=$(jq -r '.label // "parked"' "$record")
  cwd=$(jq -r '.cwd // empty' "$record")
  if [[ -z "$cwd" || ! -d "$cwd" ]]; then
    echo "park レコードの cwd がありません: ${cwd:-(未記録)}"
    return 1
  fi

  # レコードの session が別 pane で生きているなら二重に開かない。park は「閉じてから
  # 戻る」もので、元の workspace を残したまま復元すると同じ会話が 2 箇所で開く。
  local agents live=0 sid
  agents=$(herdr agent list)
  for sid in ${(f)"$(jq -r '.panes[]?.session_id // empty' "$record")"}; do
    if jq -e --arg s "$sid" '[.result.agents[] | select(.agent_session.value == $s)] | length > 0' \
         <<< "$agents" >/dev/null; then
      echo "  まだ動いています: $sid"
      live=1
    fi
  done
  if (( live )); then
    echo "上の session が別 pane で生きています。先にその workspace を閉じてから hunpark してください。"
    return 1
  fi

  local resp root_pane
  resp=$(herdr workspace create --cwd "$cwd" --label "$label" --focus) || return 1
  root_pane=$(jq -r '.result.root_pane.pane_id // empty' <<< "$resp")
  if [[ -z "$root_pane" ]]; then
    echo "failed to create herdr workspace"
    return 1
  fi

  # レコードの pane を順に復元する。1 つ目は root pane、2 つ目以降は直前の pane の
  # 右へ split する（root を基準にすると 3 つ目以降が逆順に挿し込まれるため）。
  local n=0 target prev agent session pane_cwd cmd
  while IFS=$'\t' read -r agent session pane_cwd; do
    [[ -z "$agent" ]] && continue
    if (( n == 0 )); then
      target="$root_pane"
    else
      target=$(herdr pane split --pane "$prev" --direction right \
                 --cwd "${pane_cwd:-$cwd}" --no-focus | jq -r '.result.pane.pane_id // empty')
      [[ -z "$target" ]] && break
    fi
    prev="$target"
    case "$agent" in
      claude) [[ -n "$session" ]] && cmd="claude --resume $session" || cmd="claude" ;;
      codex)  [[ -n "$session" ]] && cmd="codex resume $session"   || cmd="codex" ;;
      *)      cmd="" ;;
    esac
    [[ -n "$cmd" ]] && herdr pane run "$target" ${=cmd} >/dev/null
    (( n++ ))
  done < <(jq -r '.panes[]? | [(.agent // ""), (.session_id // ""), (.cwd // "")] | @tsv' "$record")

  # 再開したので park を解除する（hclean の判定から外すため）
  mkdir -p "$dir/resumed"
  mv "$record" "$dir/resumed/" 2>/dev/null
  [[ -f "${record%.json}.md" ]] && mv "${record%.json}.md" "$dir/resumed/" 2>/dev/null

  # resumed は「何を待っていたか」の履歴として残すが、放っておくと park も
  # workspace と同じように溜まるので 30 日で剪定する。
  find "$dir/resumed" -maxdepth 1 -type f -mtime +30 -delete 2>/dev/null

  echo "resumed: $label ($cwd)"
  echo "park メモ: $dir/resumed/${${record:t}%.json}.md"
}
