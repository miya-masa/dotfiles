#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

npm i -g @redocly/openapi-cli@latest
npm i -g redoc-cli
npm i -g prettier
npm i -g write-good
npm i -g markdownlint-cli
