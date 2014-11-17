
@echo off

rem
rem このバッチの説明
rem

rem 設定事項
set HOGE="変数の値"

rem このバッチが存在するフォルダをカレントに
pushd %0\..
cls

cd C:\Users\%USERNAME%
del .\_vimrc
mklink .\_vimrc .\dotfiles\_vimrc 
del .\_gvimrc
mklink .\_gvimrc .\dotfiles\_gvimrc 
rd .\.vim
mklink /D .\.vim .\dotfiles\.vim 
pushd %0\..

pause
exit
