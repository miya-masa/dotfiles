# dotfiles

1. kaoriya-vimをダウンロード/任意の場所に解凍
2. msys-gitをインストール
3. git-bashを開き以下のコマンドを実行

  ```
  curl https://raw.githubusercontent.com/Shougo/dein.vim/master/bin/installer.sh > installer.sh
  sh ./installer.sh ~.cache/dein
  ```
4. _vimrcおよび_gvimrcをホームディレクトリに配置
5. vimXX/switches/catalog/utf-8.vimをvimXX/switches/enbaledにコピー
6. vimXX/plugins/vimproc/lib/vimproc_win64.dllを$HOME/.cache/dein/repos/github.com/Shougo/vimproc.vim/libにコピー
7. npm install -g esformatter eslint eslint-config-standard eslint-plugin-promise eslint-plugin-standard
> => (esformatterのlcdがバグってるのでスペース一個入れる)
