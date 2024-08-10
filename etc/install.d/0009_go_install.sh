#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

PATH="~/.local/share/mise/shims:$PATH"
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/mattn/memo@latest
go install github.com/google/gops@latest
go install github.com/cweill/gotests/gotests@latest
go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest
go install go.uber.org/mock/mockgen@latest
go install github.com/google/wire/cmd/wire@latest
go install github.com/fatih/gomodifytags@latest
go install github.com/josharian/impl@master
go install mvdan.cc/sh/v3/cmd/shfmt@latest
