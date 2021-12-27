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
XDG_CONFIG_HOME=${XDG_CONFIG_HOME}
SSH_PASSPHRASE=${SSH_PASSPHRASE:-""}

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
  sudo apt update -y

  if [[ ! -d ${DOTFILES_DIRECTORY} ]]; then
    if ! has git; then
      sudo apt install -y git
    fi
    git clone http://github.com/miya-masa/dotfiles.git -b ${DOTFILES_BRANCH} ${DOTFILES_DIRECTORY}
    cd ${DOTFILES_DIRECTORY}
  fi
  cd ${DOTFILES_DIRECTORY}
  if [[ ${UNAME} == "Linux" ]]; then
    _initialize_linux
  else
    _initialize_mac
  fi
  git remote set-url origin git@github.com:miya-masa/dotfiles.git
  echo "Successful!! Restart your machine."
}

function _initialize_linux() {
  for i in "${DOTFILES_DIRECTORY}"/etc/install.d/*.sh ; do
    echo "Installing: "`basename ${i}`
    source "${i}"
  done

  SSH_RSA=~/.ssh/id_rsa
  if [ ! -s ${SSH_RSA} ]; then
    if [ "${SSH_PASSPHRASE}" = "" ]; then
      printf "ssh key passphrase: "
      read -s SSH_PASSPHRASE
    fi
    ssh-keygen -P ${SSH_PASSPHRASE} -f ${SSH_RSA}
  fi

  SSH_ECDSA=~/.ssh/id_ecdsa
  if [ ! -s ${SSH_ECDSA} ]; then
    if [ "${SSH_PASSPHRASE}" = "" ]; then
      printf "ssh key passphrase: "
      read -s SSH_PASSPHRASE
    fi
    ssh-keygen -t ecdsa -b 384 -P ${SSH_PASSPHRASE} -f ${SSH_ECDSA}
  fi

  SSH_ED25519=~/.ssh/id_ed25519
  if [ ! -s ${SSH_ED25519} ]; then
    if [ "${SSH_PASSPHRASE}" = "" ]; then
      printf "ssh key passphrase: "
      read -s SSH_PASSPHRASE
    fi
    ssh-keygen -t ed25519 -P ${SSH_PASSPHRASE} -f ${SSH_ED25519}
  fi

  deploy

  if [[ ${CI} != "true" ]]; then
    chsh -s $(which zsh)
  fi
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
  ln -fs ${DOTFILES_DIRECTORY}/.fzf.zsh ${HOME}/.fzf.zsh
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
