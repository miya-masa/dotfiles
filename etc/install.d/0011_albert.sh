#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

if ! has albert ; then
  echo "Install albert"

  sudo rpm --import "https://build.opensuse.org/projects/home:manuelschneid3r/public_key"
  curl https://build.opensuse.org/projects/home:manuelschneid3r/public_key | sudo apt-key add -
  UBUNTU_VERSION=20.04
  echo "deb http://download.opensuse.org/repositories/home:/manuelschneid3r/xUbuntu_${UBUNTU_VERSION}/ /" | sudo tee /etc/apt/sources.list.d/home:manuelschneid3r.list
  sudo wget -nv https://download.opensuse.org/repositories/home:manuelschneid3r/xUbuntu_${UBUNTU_VERSION}/Release.key -O "/etc/apt/trusted.gpg.d/home:manuelschneid3r.asc"
  sudo apt update -y
  sudo apt install -y albert
fi

