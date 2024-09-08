#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

npm i -g @redocly/cli@latest
npm i -g redoc-cli
npm i -g prettier
npm i -g write-good
npm i -g markdownlint-cli
npm i -g md-to-pdf
npm i -g commitizen
npm i -g cz-git
npm i -g markdownlint
npm i -g prettier
