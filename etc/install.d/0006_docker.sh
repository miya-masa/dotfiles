#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

if ! has docker; then
  curl -fsSL https://get.docker.com | sh || true
  curl -fsSL https://get.docker.com/rootless | sh || true
fi
