#!/usr/bin/env bash
set -euo pipefail

git_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf '%s\n' 'Not inside a git repository.'
  exit 1
}

commit_msg_file=$(git rev-parse --git-path COMMIT_EDITMSG)
if [[ "$commit_msg_file" != /* ]]; then
  commit_msg_file="$git_root/$commit_msg_file"
fi

editor=${LAZYGIT_EDIT_COMMAND:-}
if [[ -z "$editor" ]]; then
  editor=nvim
fi

diff=$(git diff --staged)
if [[ -n "$diff" ]]; then
  prompt=$(
    cat <<'EOF'
You are an assistant that writes git commit messages.
Use the project's commit message skill.
Return only the commit message, no code fences, no extra text.
Diff:
EOF
  )
  message=$(printf '%s\n%s' "$prompt" "$diff" | claude -p 2>/dev/null || true)
  if [[ -n "${message//[[:space:]]/}" ]]; then
    printf '%s\n' "$message" >"$commit_msg_file"
  fi
fi

"$editor" "$commit_msg_file"
