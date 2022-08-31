#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
