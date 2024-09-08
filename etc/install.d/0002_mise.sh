#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

LDFLAGS="-L$(brew --prefix openssl@1.1)/lib"
export LDFLAGS
CPPFLAGS="-I$(brew --prefix openssl@1.1)/include"
export CPPFLAGS
PKG_CONFIG_PATH="$(brew --prefix openssl@1.1)/lib/pkgconfig"
export PKG_CONFIG_PATH

curl https://mise.run | sh
if ! has mise; then
  export PATH="$HOME/.local/bin:$PATH"
  __shell_name=$(basename "$SHELL")
  eval "$(~/.local/bin/mise activate "${__shell_name}")"
fi
mise --version
mise install -y
