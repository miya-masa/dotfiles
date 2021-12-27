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
  if ! has git; then
    echo ${password} | sudo -Ssudo apt install git
  fi
  echo ${password} | sudo -S apt-get update
  git clone http://github.com/miya-masa/dotfiles.git ${DOTFILES_DIRECTORY}
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
    uuid-dev \
    xsel \
    zlib1g-dev \
    zsh
  if ! has pyenv ; then
    curl https://pyenv.run | bash
  fi
  PYENV_SHIMS=$(pyenv root)/shims
  PYTHON_VERSION=3.10.1
  pyenv install -f ${PYTHON_VERSION}
  pyenv global ${PYTHON_VERSION}
  ${PYENV_SHIMS}/python -V
  ${PYENV_SHIMS}/python -m pip install --upgrade pip
  ${PYENV_SHIMS}/python 
  ${PYENV_SHIMS}/pip install pynvim
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
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
    eval $(~/.linuxbrew/bin/brew shellenv)
    eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
  fi
  brew bundle --file=./Brewfile_linux
  curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add -
  echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
}


function _initialize_mac() {
  echo TODO
}


function password() {
    printf "sudo password: "
    read -s password
}

function deploy() {
  echo deploy
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
