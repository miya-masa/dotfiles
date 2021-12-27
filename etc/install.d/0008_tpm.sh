#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

if [ ! -d ~/.tmux/plugins/tpm ] ; then
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

