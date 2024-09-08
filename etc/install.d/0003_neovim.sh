#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

# sudo コマンドをラップする関数
sudo_wrap() {
    if [ -n "$SUDO_ASKPASS" ]; then
        sudo -A "$@"
    else
        sudo "$@"
    fi
}

PATH="~/.local/share/mise/shims:$PATH"
curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage
chmod u+x nvim.appimage
sudo_wrap mv ./nvim.appimage /usr/bin/nvim
npm install -g neovim
pip install pynvim
