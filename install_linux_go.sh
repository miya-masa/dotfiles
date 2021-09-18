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

GOVERSION=1.17

_install() {
  sudo rm -rf /usr/local/go
  curl -L -O https://golang.org/dl/go${GOVERSION}.linux-amd64.tar.gz
  sudo tar -C /usr/local -xzf go${GOVERSION}.linux-amd64.tar.gz
  sudo chown $USER:$USER  -R /usr/local/go
  rm go${GOVERSION}.linux-amd64.tar.gz
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
