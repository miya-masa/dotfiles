#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

if [ ! -d ~/nerd-fonts ] ; then
  git clone https://github.com/ryanoasis/nerd-fonts.git --depth 1 ~/nerd-fonts
fi
git pull
cd ~/nerd-fonts
./install.sh IBMPlexMono
./install.sh FiraCode
./install.sh FiraMono
./install.sh Hack
./install.sh Hasklig
