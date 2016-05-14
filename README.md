# dotfiles

1. kaoriya-vimをダウンロード/任意の場所に解凍
2. msys-gitをインストール
3. git-bashを開き以下のコマンドを実行

  ```
  curl https://raw.githubusercontent.com/Shougo/neobundle.vim/master/bin/install.sh > install.sh
  sh /install.sh
  ```
4. _vimrcおよび_gvimrcをホームディレクトリに配置
5. vimXX/switches/catalog/utf-8.vimをvimXX/switches/enbaledにコピー
6. vimXX/plugins/vimproc/lib/vimproc_win64.dllを$HOME/.vim/bundle/vimproc.vim/lib/にコピー
7. npm install -g esformatter eslint eslint-config-standard eslint-plugin-promise eslint-plugin-standard
> => (esformatterのlcdがバグってるのでスペース一個入れる)
