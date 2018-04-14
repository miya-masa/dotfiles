#!/bin/sh

cd $(dirname $0)

mkdir -p ~/.config/nvim
mkdir -p ~/.vim/snippets/javascript

for dotfile in `find ./ -type d -name '.git' -prune -o -type f -and -print`
do
  rm -f "$HOME/$dotfile"
  ln -s "$PWD/$dotfile" "$HOME/$dotfile"
done
