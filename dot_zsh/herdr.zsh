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
