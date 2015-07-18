@echo off

rem
rem このバッチの説明
rem

rem 設定事項
set HOGE="変数の値"

rem このバッチが存在するフォルダをカレントに
pushd %0\..
cls

 curl https://raw.githubusercontent.com/Shougo/neobundle.vim/master/bin/install.sh | sh
cd C:\Users\%USERNAME%
del .\_vimrc
mklink .\_vimrc .\dotfiles\_vimrc
del .\_gvimrc
mklink .\_gvimrc .\dotfiles\_gvimrc
del .\.bash_profile
mklink .\_bash_profile .\dotfiles\.bash_profile
del .\.editorconfig
mklink .\.editorconfig .\dotfiles\.editorconfig
del .\.jshintrc
mklink .\.jshintrc .\dotfiles\.jshintrc
del .\.vimshrc
mklink .\.vimshrc .\dotfiles\.vimshrc
pushd %0\..

pause
exit
