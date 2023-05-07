#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

mkdir ~/tree-sitters
cd ~/tree-sitters
git clone https://github.com/gleam-lang/tree-sitter-gleam.git
tree-sitter parse
