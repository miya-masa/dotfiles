#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

GOVERSION=1.19

sudo rm -rf /usr/local/go
curl -L -O https://golang.org/dl/go${GOVERSION}.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go${GOVERSION}.linux-amd64.tar.gz
sudo chown $USER:$USER  -R /usr/local/go
rm go${GOVERSION}.linux-amd64.tar.gz

export PATH=/usr/local/go/bin:${PATH}
