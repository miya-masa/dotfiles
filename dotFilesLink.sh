#! /bin/bash

ln -s ~/dotfiles/_vimrc ~/.vimrc
ln -s ~/dotfiles/_gvimrc ~/.gvimrc
ln -s ~/dotfiles/.gitconfig ~/.gitconfig
curl https://raw.githubusercontent.com/Shougo/neobundle.vim/master/bin/install.sh | sh
mkdir -p ~/.vim/bundle
git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
