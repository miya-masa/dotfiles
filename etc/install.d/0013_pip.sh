#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

pip install \
  pgcli \
  mycli \
  black \
  isort \
  flake8 \
  mypy \
  pyls-flake8 \
  pylsp-mypy \
  pyls-isort \
  python-lsp-black
