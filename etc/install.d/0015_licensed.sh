#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

if [[ ! -e /usr/local/bin/licensed ]]; then
  curl -sSL https://github.com/github/licensed/releases/download/3.4.0/licensed-3.4.0-linux-x64.tar.gz > licensed.tar.gz
  tar -xzf licensed.tar.gz
  rm -f licensed.tar.gz
  rm -rf ./meta
  sudo mv licensed /usr/local/bin
  sudo chown root:root /usr/local/bin/licensed
fi
