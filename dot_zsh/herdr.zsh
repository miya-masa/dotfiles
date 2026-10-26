# Herdr 内の Codex TUI は、CLI の暗黙的な共有 daemon を再利用せず embedded backend
# を使うよう、root の argv を最小限 scan して local override を先頭に追加する。
# 管理 subcommand、明示的な remote/help/version、未知の root option は素通しする。
# 現在の Codex CLI 0.154.0 の root parser を対象にしており、未知の subcommand と prompt
# は区別できないため、既知の管理 subcommand だけを素通し判定する。
if [[ "${HERDR_ENV:-}" == 1 ]]; then
  _herdr_codex_tui_args() {
    local token
    local i=1
    local image_files
    local -a scan_args
    scan_args=("$@")

    # resume の後でも、`--` より前の明示指定を優先する。
    while (( i <= $# )); do
      token="${scan_args[i]}"
      [[ "$token" == "--" ]] && break
      case "$token" in
        --remote|--remote=*|-h|--help|-V|--version) return 1 ;;
      esac
      (( i++ ))
    done

    i=1
    while (( i <= $# )); do
      token="${scan_args[i]}"
      [[ "$token" == "--" ]] && return 0
      case "$token" in
        -c|--config|--enable|--disable|--remote-auth-token-env|-m|--model|--local-provider|-p|--profile|-s|--sandbox|-C|--cd|--add-dir|-a|--ask-for-approval)
          (( i++ ))
          (( i > $# )) && return 1
          (( i++ ))
          ;;
        --config=*|--enable=*|--disable=*|--remote-auth-token-env=*|--model=*|--local-provider=*|--profile=*|--sandbox=*|--cd=*|--add-dir=*|--ask-for-approval=*)
          (( i++ ))
          ;;
        -c?*|-m?*|-p?*|-s?*|-C?*|-a?*)
          (( i++ ))
          ;;
        -i|--image)
          (( i++ ))
          image_files=0
          while (( i <= $# )); do
            token="${scan_args[i]}"
            [[ "$token" == "--" || "$token" == -* ]] && break
            image_files=1
            (( i++ ))
          done
          (( image_files )) || return 1
          ;;
        --image=*|-i?*)
          (( i++ ))
          ;;
        --strict-config|--oss|--approve-for-me|--dangerously-bypass-approvals-and-sandbox|--dangerously-bypass-hook-trust|--worktree|--search|--no-alt-screen)
          (( i++ ))
          ;;
        agents|exec|e|review|login|logout|mcp|plugin|app-server|exec-server|remote-control|completion|update|doctor|sandbox|debug|apply|a|queue|archive|delete|migrate-rollouts|unarchive|cloud|features|help)
          return 1
          ;;
        -*)
          return 1
          ;;
        *)
          return 0
          ;;
      esac
    done
    return 0
  }

  codex() {
    if [[ "${HERDR_ENV:-}" != 1 ]]; then
      command codex "$@"
      return $?
    fi
    if _herdr_codex_tui_args "$@"; then
      command codex -c 'shell_environment_policy.set.HERDR_ENV="1"' "$@"
      return $?
    fi
    command codex "$@"
    return $?
  }
fi

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
          --header='TAB=選択 / ok=閉じてよい WARN=要確認 busy=稼働中 (クエリを消せば全件)' \
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
