
@echo off

rem
rem ���̃o�b�`�̐���
rem

rem �ݒ莖��
set HOGE="�ϐ��̒l"

rem ���̃o�b�`�����݂���t�H���_���J�����g��
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
