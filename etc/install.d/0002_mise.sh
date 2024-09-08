#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

[ -f /home/linuxbrew/.linuxbrew/bin/brew ] && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
# curl https://mise.run | sh | sh
# if ! has mise; then
#   export PATH="$HOME/.local/bin:$PATH"
#   __shell_name=$(basename "$SHELL")
#   eval "$(~/.local/bin/mise activate "${__shell_name}")"
# fi
mise --version
mise install -y
