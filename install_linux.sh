#!/usr/bin/env bash
#
# Usage:
#   install_linux.sh
#
# Depends on:
#

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

# $_ME
#
# Set to the program's basename.
_ME=$(basename "")

###############################################################################
# Help
###############################################################################

# _print_help()
#
# Usage:
#   _print_help
#
# Print the program help information.
_print_help() {
  cat <<HEREDOC

Usage:
  ${_ME} [<arguments>]
  ${_ME} -h | --help

Options:
  -h --help  Show this screen.
HEREDOC
}

###############################################################################
# Program Functions
###############################################################################

_install() {
  sudo apt update
  sudo add-apt-repository universe
  sudo apt install -y curl
  sudo apt install -y \
    autojump \
    asciidoc \
    build-essential \
    gawk \
    gcc make \
    gnome-tweak-tool \
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
    libxml2-dev
    libyaml-dev \
    mycli \
    nodejs \
    npm \
    pgcli \
    pkg-config autoconf automake \
    ripgrep \
    tk-dev
    uuid-dev \
    xsel \
    zlib1g-dev \
    zsh
  curl https://pyenv.run | bash
  source ~/.zshrc
  sudo pip3 install pynvim
  sudo npm install -g neovim
  rm -rf ctags
  git clone https://github.com/universal-ctags/ctags.git
  cd ctags
  sudo ./autogen.sh
  sudo ./configure
  sudo make
  sudo make install
  cd ../
  sudo rm -rf ctags
  if !(type "brew" > /dev/null 2>&1); then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    test -d ~/.linuxbrew && eval $(~/.linuxbrew/bin/brew shellenv)
    test -d /home/linuxbrew/.linuxbrew && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
    test -r ~/.bash_profile && echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.bash_profile
    echo "eval \$($(brew --prefix)/bin/brew shellenv)" >>~/.profile
  fi
  brew bundle --file=./Brewfile_linux
  curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add -
  echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
  ./install_linux_go.sh
}

###############################################################################
# Main
###############################################################################

_main() {
  if [[ "-" =~ ^-h|--help$  ]]
  then
    _print_help
  else
    _install
  fi
}

_main
