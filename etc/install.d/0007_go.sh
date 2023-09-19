#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

sudo apt-get install bison
if [[ ! -f ${HOME}/.gvm/scripts/gvm ]]; then
  bash < <(GVM_NO_UPDATE_PROFILE=true curl -s -S -L https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer) || true
  zsh -c "source ${HOME}/.gvm/scripts/gvm"
fi

gvm install go1.4 -B
gvm use go1.4
export GOROOT_BOOTSTRAP=$GOROOT
gvm install go1.17.13
gvm use go1.17.13
export GOROOT_BOOTSTRAP=$GOROOT
gvm install go1.20
gvm use go1.20.7 --default
