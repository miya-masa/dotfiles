#! /bin/bash

ln -s ~/dotFiles/_vimrc ~/.vimrc
ln -s ~/dotFiles/_gvimrc ~/.gvimrc
ln -s ~/dotFiles/.gitconfig ~/.gitconfig
curl https://raw.githubusercontent.com/Shougo/neobundle.vim/master/bin/install.sh | sh
mkdir -p ~/.vim/bundle
git clone https://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim
