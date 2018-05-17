#!/bin/sh

cd $(dirname $0)

mkdir -p ~/.config/nvim
mkdir -p ~/.vim/snippets/javascript

for dotfile in `find ./ -type d -name '.git' -prune -o -type f -and -print`
do
  rm -f "$HOME/$dotfile"
  ln -s "$PWD/$dotfile" "$HOME/$dotfile"
done

if [ ! -e $HOME/.fzf ]; then
  echo clone fzf
  git clone --depth 1 https://github.com/junegunn/fzf.git $HOME/.fzf
fi

$HOME/.fzf/install

if [ -e $HOME/.fzf.zsh ]; then
  echo "source ~/.fzfadd.zsh" >> $HOME/.fzf.zsh
fi
