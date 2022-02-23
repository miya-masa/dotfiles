#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

go install github.com/nametake/golangci-lint-langserver@latest
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/mattn/memo@latest
go install github.com/google/gops@latest
go install github.com/cweill/gotests/gotests@latest
go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest
go install github.com/golang/mock/mockgen@v1.6.0
go install github.com/google/wire/cmd/wire@v0.5.0
go install github.com/fatih/gomodifytags@latest
