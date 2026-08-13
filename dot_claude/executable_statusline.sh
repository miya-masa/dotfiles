#!/usr/bin/env bash
# Claude Code status line — reads JSON from stdin, outputs formatted status
set -uo pipefail

INPUT=$(cat)

# --- Parse fields (field names confirmed from actual JSON) ---
MODEL=$(echo "$INPUT" | jq -r '.model.display_name // empty' 2>/dev/null || echo "")
CTX_USED=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0')
CTX_SIZE=$(echo "$INPUT" | jq -r '.context_window.context_window_size // 0')
COST_USD=$(echo "$INPUT" | jq -r '.cost.total_cost_usd // 0')
LINES_ADD=$(echo "$INPUT" | jq -r '.cost.total_lines_added // 0')
LINES_DEL=$(echo "$INPUT" | jq -r '.cost.total_lines_removed // 0')
RATE_5H=$(echo "$INPUT" | jq -r '.rate_limits.five_hour.used_percentage // empty' 2>/dev/null || echo "")
RATE_7D=$(echo "$INPUT" | jq -r '.rate_limits.seven_day.used_percentage // empty' 2>/dev/null || echo "")
CWD_JSON=$(echo "$INPUT" | jq -r '.workspace.current_dir // empty' 2>/dev/null || echo "")

# --- Shortened cwd ---
CWD="${CWD_JSON:-$(pwd)}"
CWD=$(echo "$CWD" | sed "s|^$HOME|~|")
if [ "$(echo "$CWD" | tr '/' '\n' | wc -l)" -gt 3 ]; then
  CWD="…/$(echo "$CWD" | rev | cut -d'/' -f1-2 | rev)"
fi

# --- Color-code context usage ---
if [ "$CTX_USED" -ge 50 ]; then
  CTX_ICON="🔴"
elif [ "$CTX_USED" -ge 30 ]; then
  CTX_ICON="🟡"
else
  CTX_ICON="🟢"
fi

# --- Format context size (1000000 -> 1M) ---
if [ "$CTX_SIZE" -ge 1000000 ]; then
  CTX_SIZE_FMT="$((CTX_SIZE / 1000000))M"
elif [ "$CTX_SIZE" -ge 1000 ]; then
  CTX_SIZE_FMT="$((CTX_SIZE / 1000))k"
else
  CTX_SIZE_FMT="$CTX_SIZE"
fi

# --- Format cost ---
COST_FMT=$(printf '%.2f' "$COST_USD")

# --- Build output ---
PARTS=()

# Model (shorten display name)
if [ -n "$MODEL" ] && [ "$MODEL" != "null" ]; then
  SHORT_MODEL=$(echo "$MODEL" | sed 's/ (.*)//')
  PARTS+=("$SHORT_MODEL")
fi

# Context usage
PARTS+=("${CTX_ICON} ${CTX_USED}%/${CTX_SIZE_FMT}")

# Cost
if [ "$COST_FMT" != "0.00" ]; then
  PARTS+=("\$${COST_FMT}")
fi

# Lines changed
if [ "$LINES_ADD" -gt 0 ] || [ "$LINES_DEL" -gt 0 ]; then
  PARTS+=("+${LINES_ADD}/-${LINES_DEL}")
fi

# Rate limits
if [ -n "$RATE_5H" ] && [ "$RATE_5H" != "null" ]; then
  PARTS+=("5h:${RATE_5H}%")
fi
if [ -n "$RATE_7D" ] && [ "$RATE_7D" != "null" ]; then
  PARTS+=("7d:${RATE_7D}%")
fi

# --- Background agents (best-effort: count task dirs without .output) ---
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || echo "")
BG_COUNT=0
if [ -n "$SESSION_ID" ]; then
  # Task output files live under /tmp/claude-<uid>/*/tasks/
  for TASK_DIR in /tmp/claude-"$(id -u)"/*/tasks; do
    [ -d "$TASK_DIR" ] || continue
    # Running = has pid file or lock but no .output yet
    RUNNING=$(find "$TASK_DIR" -maxdepth 1 ! -name "*.output" -type f -newer "$TASK_DIR" 2>/dev/null | wc -l || echo 0)
    BG_COUNT=$((BG_COUNT + RUNNING))
  done
fi
if [ "$BG_COUNT" -gt 0 ]; then
  PARTS+=("⚡${BG_COUNT}bg")
fi

# Worktree status (wt provides: path, branch, dirty/staged, ahead/behind)
WT_STATUS=$(wt list statusline --format=claude-code 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' || echo "")
if [ -n "$WT_STATUS" ]; then
  PARTS+=("$WT_STATUS")
else
  # Fallback: git branch + CWD if wt is not available
  BRANCH=$(git -C "$(echo "$INPUT" | jq -r '.workspace.project_dir // "."')" branch --show-current 2>/dev/null || echo "")
  if [ -n "$BRANCH" ]; then
    PARTS+=("⎇ $BRANCH")
  fi
  PARTS+=("$CWD")
fi

# Join with separator
OUTPUT=""
for i in "${!PARTS[@]}"; do
  if [ "$i" -eq 0 ]; then
    OUTPUT="${PARTS[$i]}"
  else
    OUTPUT="$OUTPUT · ${PARTS[$i]}"
  fi
done
# --- session-insights: 未処理 proposal バッジ ---
SI_PROPOSALS_DIR="$HOME/.claude/data/session-insights/proposals"
SI_BADGE=""
if [[ -d "$SI_PROPOSALS_DIR" ]]; then
  si_count=$(find "$SI_PROPOSALS_DIR" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$si_count" -gt 0 ]]; then
    SI_BADGE=" 📋${si_count}"
  fi
fi
echo "${OUTPUT}${SI_BADGE}"
