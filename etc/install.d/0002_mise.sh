#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

curl https://mise.jdx.dev/install.sh | sh
if ! has mise; then
  export PATH="$HOME/.local/bin:$PATH"
fi
mise --version
sudo apt install -y pkg-config
mise install -y
