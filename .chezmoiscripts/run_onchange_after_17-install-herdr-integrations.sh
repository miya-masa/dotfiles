#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

function has() {
  type "$1" >/dev/null 2>&1
}

# herdr の agent integration を入れる。Claude / Codex では hook が native
# session identity を herdr へ渡し、server 再起動後の resume に使う。agent の
# working / blocked / done / idle は integration の有無にかかわらず screen
# manifest で判定する。
#
# hook 本体 (~/.claude/hooks/herdr-agent-state.sh、~/.codex/herdr-agent-state.sh)
# と ~/.codex/hooks.json の Herdr エントリは installer が所有する。生成 hook
# 自体は編集せず、この script が導入と chezmoi 所有の fallback 追記を行う。
#
# hook は HERDR_ENV / HERDR_SOCKET_PATH / HERDR_PANE_ID が揃わないと即 exit 0
# するため、tmux 側の cc-pane とは干渉しない。
if ! has herdr; then
  echo "⏭️  herdr not found; skipping agent integrations."
  exit 0
fi

# status の行は `<kind>: current (v7) (<path>)` / `<kind>: not installed (<path>)` /
# 版が古い場合は outdated 表記になる。current 以外はすべて入れ直す。
for kind in claude codex; do
  status_line="$(herdr integration status | grep "^${kind}:" || true)"
  case "${status_line}" in
    *": current"*)
      echo "✅ herdr ${kind} integration is up to date."
      ;;
    *)
      echo "🔧 Installing herdr ${kind} integration..."
      herdr integration install "${kind}"
      ;;
  esac
done

# Codex 0.147 may omit transcript_path from its initial SessionStart payload.
# Once a prompt has materialised the rollout, this bridge supplies that path to
# the generated Herdr hook.  Keep the generated hook and its other entries
# owned by Herdr; only merge this one chezmoi-owned command here.
codex_home="${CODEX_HOME:-${HOME}/.codex}"
python3 - "${codex_home}/hooks.json" <<'PY'
import json
import os
from pathlib import Path
import shlex
import tempfile
import sys


hooks_path = Path(sys.argv[1])
if hooks_path.exists():
    with hooks_path.open(encoding="utf-8") as hooks_file:
        document = json.load(hooks_file)
else:
    document = {}

if not isinstance(document, dict):
    raise TypeError("Codex hooks.json must contain a JSON object")

hooks = document.setdefault("hooks", {})
if not isinstance(hooks, dict):
    raise TypeError("Codex hooks.json 'hooks' must contain a JSON object")

user_prompt_hooks = hooks.setdefault("UserPromptSubmit", [])
if not isinstance(user_prompt_hooks, list):
    raise TypeError("Codex hooks.json UserPromptSubmit must contain an array")

bridge_path = Path.home() / ".local" / "bin" / "herdr-codex-session-bridge"
bridge_command = shlex.quote(str(bridge_path))
bridge_hook = {
    "command": bridge_command,
    "timeout": 10,
    "type": "command",
}

already_present = any(
    isinstance(group, dict)
    and isinstance(group.get("hooks"), list)
    and any(
        isinstance(hook, dict) and hook.get("command") == bridge_command
        for hook in group["hooks"]
    )
    for group in user_prompt_hooks
)
if not already_present:
    user_prompt_hooks.append({"hooks": [bridge_hook]})

hooks_path.parent.mkdir(parents=True, exist_ok=True)
mode = hooks_path.stat().st_mode if hooks_path.exists() else None
with tempfile.NamedTemporaryFile(
    "w",
    encoding="utf-8",
    dir=hooks_path.parent,
    prefix=hooks_path.name + ".",
    delete=False,
) as temporary:
    temporary_path = Path(temporary.name)
    json.dump(document, temporary, ensure_ascii=False, indent=2)
    temporary.write("\n")
if mode is not None:
    os.chmod(temporary_path, mode)
os.replace(temporary_path, hooks_path)
PY
