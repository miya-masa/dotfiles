#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

function has() {
  type "$1" >/dev/null 2>&1
}

# sudo コマンドをラップする関数
sudo_wrap() {
  if [ -n "${SUDO_ASKPASS:-}" ]; then
    sudo -A "$@"
  else
    sudo "$@"
  fi
}

if ! has docker; then
  # Add Docker's official GPG key:
  sudo_wrap apt-get update -y
  sudo_wrap apt-get install ca-certificates curl -y
  sudo_wrap install -m 0755 -d /etc/apt/keyrings
  sudo_wrap curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo_wrap chmod a+r /etc/apt/keyrings/docker.asc

  # Add the repository to Apt sources:
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo_wrap tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo_wrap apt-get update -y
  sudo_wrap apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
  sudo_wrap groupadd docker || true
  sudo_wrap usermod -aG docker $USER || true
  newgrp docker || true
fi
