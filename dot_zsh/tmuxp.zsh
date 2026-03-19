# tp - fzf-powered tmuxp launcher
#
# Usage: tp
#   Select a directory via fzf (from ghq + zoxide), pick a tmuxp yaml,
#   and launch a new tmux session or append to the current one.

tp() {
  # 依存コマンドのガード
  command -v tmuxp >/dev/null || { echo "tmuxp is not installed"; return 1; }
  command -v fzf >/dev/null || { echo "fzf is not installed"; return 1; }

  # ghq / zoxide のどちらかは必要
  if ! command -v ghq >/dev/null && ! command -v zoxide >/dev/null; then
    echo "ghq or zoxide is required"
    return 1
  fi

  # ① ディレクトリ選択
  local dir
  dir=$({
    command -v ghq >/dev/null && ghq list --full-path
    command -v zoxide >/dev/null && zoxide query -l
  } | sort -u | fzf --prompt='directory> ')
  [[ -z "$dir" ]] && return 0

  # ② yaml 選択
  local yamls yaml selected
  yamls=( ~/.config/tmuxp/*.(yaml|yml)(N) )

  if (( ${#yamls} == 0 )); then
    echo "No tmuxp sessions found in ~/.config/tmuxp/"
    return 1
  elif (( ${#yamls} == 1 )); then
    yaml="${yamls[1]}"
  else
    selected=$(printf '%s\n' "${yamls[@]:t}" | fzf --prompt='tmuxp config> ')
    [[ -z "$selected" ]] && return 0
    yaml="$HOME/.config/tmuxp/${selected}"
  fi

  # ③ モード選択
  local mode
  if [[ -n "$TMUX" ]]; then
    mode=$(printf '%s\n' "new" "append" | fzf --prompt='mode> ')
    [[ -z "$mode" ]] && return 0
  else
    mode="new"
  fi

  # ④ 実行
  if [[ "$mode" == "new" ]]; then
    local default_name="${dir:t}"
    local session_name
    read "session_name?Session name [${default_name}]: " || return 0
    session_name="${session_name:-$default_name}"

    if tmux has-session -t "$session_name" 2>/dev/null; then
      echo "Session '$session_name' already exists"
      return 1
    fi

    (cd "$dir" && tmuxp load -y -s "$session_name" "$yaml")
  else
    (cd "$dir" && tmuxp load -y -a "$yaml")
  fi
}
