@echo off

rem
rem ���̃o�b�`�̐���
rem

rem �ݒ莖��
set HOGE="�ϐ��̒l"

rem ���̃o�b�`�����݂���t�H���_���J�����g��
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
del .\.editorconfig
mklink .\.jshintrc .\dotfiles\.jshintrc
pushd %0\..

pause
exit
