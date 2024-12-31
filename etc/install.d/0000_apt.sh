#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

sudo apt update -y
sudo add-apt-repository universe -y
sudo apt install -y \
  asciidoc \
  curl \
  certbot \
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
  luajit \
  autoconf automake \
  rename \
  ripgrep \
  tk-dev \
  uidmap \
  uuid-dev \
  xclip \
  rpm \
  zlib1g-dev \
  libnss3-tools \
  zsh \
  mercurial \
  snapd \
  tmux \
  zsh \
  fd-find

sudo add-apt-repository ppa:zhangsongcui3371/fastfetch
sudo apt update
sudo apt install -y fastfetch
