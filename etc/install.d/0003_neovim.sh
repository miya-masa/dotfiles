#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'


curl -L https://github.com/neovim/neovim/releases/download/stable/nvim-linux64.deb > nvim-linux64.deb
sudo apt install -y ./nvim-linux64.deb
rm nvim-linux64.deb
npm install -g neovim
pip install pynvim
