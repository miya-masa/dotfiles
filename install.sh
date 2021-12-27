#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

__ScriptVersion="v0.1.0"
UNAME=$(uname)
DOTFILES_DIRECTORY=${DOTFILES_DIRECTORY:-~/dotfiles}
DOTFILES_BRANCH=${DOTFILES_BRANCH:-master}

#===  FUNCTION  ================================================================
#         NAME:  usage
#  DESCRIPTION:  Display usage information.
#===============================================================================
function usage ()
{
  echo "Usage :  $0 [options] [comand]

    Command:
      deploy: Deploy dotfiles.
      initialize: Install software and tools.
    Options:
      -h|help       Display this message
      -v|version    Display script version"
}    # ----------  end of function usage  ----------

function has() {
  type "$1" > /dev/null 2>&1
}

function initialize() {
  if [[ -d ${DOTFILES_DIRECTORY} ]]; then
    echo "already exist ${DOTFILES_DIRECTORY}"
    exit 1
  fi
  password
  echo ${password} | sudo -S apt update -y
  if ! has git; then
    sudo apt install -y git
  fi
  git clone http://github.com/miya-masa/dotfiles.git -b ${DOTFILES_BRANCH} ${DOTFILES_DIRECTORY}
  cd ${DOTFILES_DIRECTORY}
  if [[ ${UNAME} == "Linux" ]]; then
    _initialize_linux
  else
    _initialize_mac
  fi
}

function _initialize_linux() {
  sudo apt update
  sudo add-apt-repository universe
  sudo apt install -y \
    autojump \
    asciidoc \
    curl \
    build-essential \
    dbus-user-session \
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
    libxml2-dev \
    libyaml-dev \
    mycli \
    pgcli \
    pkg-config autoconf automake \
    ripgrep \
    tk-dev \
    uidmap \
    uuid-dev \
    xsel \
    zlib1g-dev \
    zsh

  PYENV_ROOT=~/.pyenv
  if [ ! -d ${PYENV_ROOT} ]; then
    curl https://pyenv.run | bash
  fi
  PYENV_SHIMS=${PYENV_ROOT}/shims
  PYTHON_VERSION=3.10.1

  ${PYENV_ROOT}/bin/pyenv install --skip-existing ${PYTHON_VERSION}
  ${PYENV_ROOT}/bin/pyenv global ${PYTHON_VERSION}
  ${PYENV_SHIMS}/python -V
  ${PYENV_SHIMS}/python -m pip install --upgrade pip
  ${PYENV_SHIMS}/pip install pynvim
  NVM_VERSION=v0.39.1
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh | bash
  export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  NODE_VERSION=v16.13.1
  nvm install ${NODE_VERSION}
  node -v
  npm install -g neovim
  rm -rf ctags
  git clone https://github.com/universal-ctags/ctags.git
  cd ctags
  sudo ./autogen.sh
  sudo ./configure
  sudo make
  sudo make install
  cd ../
  sudo rm -rf ctags
  if ! has brew ; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
  fi
  brew bundle --file=./Brewfile_linux

  GOVERSION=1.17
  sudo rm -rf /usr/local/go
  curl -L -O https://golang.org/dl/go${GOVERSION}.linux-amd64.tar.gz
  sudo tar -C /usr/local -xzf go${GOVERSION}.linux-amd64.tar.gz
  sudo chown $USER:$USER  -R /usr/local/go
  rm go${GOVERSION}.linux-amd64.tar.gz

  if ! has docker ; then
    curl -fsSL https://get.docker.com | sh
  fi
  curl -fsSL https://get.docker.com/rootless | sh
  if [ ! -d ~/.tmux/plugins/tpm ] ; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
  fi 
  if [ ! -d ~/nerd-fonts ] ; then
    git clone https://github.com/ryanoasis/nerd-fonts.git --depth 1 ~/nerd-fonts
    cd ~/nerd-fonts
    ./install.sh IBMPlexMono
  fi
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

  deploy

  chsh -s $(which zsh)
  echo "Successful!! Restart your machine."
}


function _initialize_mac() {
  echo TODO
}


function password() {
    password=""
    printf "sudo password: "
    read -s password
}

function deploy() {
  mkdir -p ${HOME}/.tmux
  mkdir -p ${HOME}/.vim
  mkdir -p ${HOME}/.config
  ln -fs ${DOTFILES_DIRECTORY}/.tmux/tmuxline.conf ${HOME}/.tmux/tmuxline.conf
  ln -fs ${DOTFILES_DIRECTORY}/.tmux.conf ${HOME}/.tmux.conf
  ln -fs ${DOTFILES_DIRECTORY}/.tmux.conf.local ${HOME}/.tmux.conf.local
  ln -fs ${DOTFILES_DIRECTORY}/.zshrc ${HOME}/.zshrc
  ln -fs ${DOTFILES_DIRECTORY}/.zshrc_linux ${HOME}/.zshrc_linux
  ln -fs ${DOTFILES_DIRECTORY}/.zshrc_darwin ${HOME}/.zshrc_darwin
  ln -fs ${DOTFILES_DIRECTORY}/.p10k.zsh ${HOME}/.p10k.zsh
  ln -fs ${DOTFILES_DIRECTORY}/.zprofile ${HOME}/.zprofile
  ln -fs ${DOTFILES_DIRECTORY}/.gitconfig ${HOME}/.gitconfig
  ln -fs ${DOTFILES_DIRECTORY}/.vim/vimrcs ${HOME}/.vim
  ln -fs ${DOTFILES_DIRECTORY}/.config/nvim ${HOME}/.config
  ln -fs ${DOTFILES_DIRECTORY}/.config/alacritty ${HOME}/.config
}

#-----------------------------------------------------------------------
#  Handle command line arguments
#-----------------------------------------------------------------------

while getopts ":hv" opt
do
  case $opt in

  h )  usage; exit 0   ;;
  v )  echo "$0 -- Version $__ScriptVersion"; exit 0   ;;
  * )  echo -e "\n  Option does not exist : $OPTARG\n"
      usage; exit 1   ;;

  esac    # --- end of case ---
done


case ${1:-initialize} in
  deploy ) deploy; exit 0 ;;
  initialize ) initialize; exit 0 ;;
  * ) echo "Unknown command $1"
esac
