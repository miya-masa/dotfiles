#!/bin/sh

if [ ! -e $HOME/.fzf ]; then
  echo clone fzf
  git clone --depth 1 https://github.com/junegunn/fzf.git $HOME/.fzf
fi

$HOME/.fzf/install

if [ -e $HOME/.fzf.zsh ]; then
  echo "source ~/.fzfadd.zsh" >> $HOME/.fzf.zsh
fi