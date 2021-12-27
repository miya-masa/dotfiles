#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

rm -rf ctags
git clone https://github.com/universal-ctags/ctags.git
cd ctags
sudo ./autogen.sh
sudo ./configure
sudo make
sudo make install
cd ../
sudo rm -rf ctags
