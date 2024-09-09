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

if ! has op; then
  curl -sS https://downloads.1password.com/linux/keys/1password.asc |
    sudo_wrap gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" |
    sudo_wrap tee /etc/apt/sources.list.d/1password.list
  sudo_wrap mkdir -p /etc/debsig/policies/AC2D62742012EA22/
  curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol |
    sudo_wrap tee /etc/debsig/policies/AC2D62742012EA22/1password.pol
  sudo_wrap mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22
  curl -sS https://downloads.1password.com/linux/keys/1password.asc |
    sudo_wrap gpg --dearmor --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg
  sudo_wrap apt update && sudo_wrap apt install 1password-cli
fi
op --version
