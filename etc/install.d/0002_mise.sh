#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

curl https://mise.jdx.dev/install.sh | sh
eval "$(~/.local/bin/mise activate bash)"
mise --version
mise install -y
