#!/usr/bin/env bash
set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

# set tmux panes for ide
  tmux split-window -v
  tmux split-window -h
  tmux select-pane -t 1
  tmux split-window -h
  tmux select-pane -t 1
  tmux resize-pane -D 15
