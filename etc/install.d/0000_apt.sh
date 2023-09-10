#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'


sudo apt update
sudo add-apt-repository universe
sudo apt install -y \
  autojump \
  asciidoc \
  curl \
  build-essential \
  dbus-user-session \
  fcitx \
  fcitx-mozc \
  fuse \
  gawk \
  gcc make \
  gnome-tweaks \
  gtk2-engines-murrine gtk2-engines-pixbuf \
  keychain \
  libbz2-dev \
  libdb-dev \
  libffi-dev \
  libgdbm-dev \
  libjansson-dev \
  liblzma-dev \
  libncursesw5-dev \
  libreadline-dev \
  libseccomp-dev \
  libsqlite3-dev \
  libssl-dev \
  libxml2-dev \
  libyaml-dev \
  libpq-dev \
  openssh-server \
  pkg-config autoconf automake \
  rename \
  ripgrep \
  tk-dev \
  uidmap \
  uuid-dev \
  xsel \
  rpm \
  zlib1g-dev \
  python3-docutils \
  libnss3-tools \
  zsh \
  neofetch \
  mercurial \
  snapd \
  fd-find

sudo cp .config/neofetch/banner.txt /etc/update-motd.d/
if ! sudo grep -q "$HOME/.config/neofetch/config.conf" /etc/update-motd.d/00-header; then
  sudo echo "$HOME/.config/neofetch/config.conf" | sudo tee -a /etc/update-motd.d/00-header
fi

