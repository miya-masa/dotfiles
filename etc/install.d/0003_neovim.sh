#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

# sudo コマンドをラップする関数
sudo_wrap() {
  if [ -n "${SUDO_ASKPASS:-}" ]; then
    sudo -A "$@"
  else
    sudo "$@"
  fi
}

export PATH="~/.local/share/mise/shims:$PATH"

# Neovimの最新バージョン取得
#
NVIM_VERSION=$(curl -s https://api.github.com/repos/neovim/neovim/releases/latest | grep -Po '"tag_name": "\K[^"]*')
echo "Installing Neovim version: $NVIM_VERSION"

# ダウンロードURL（x86_64用）
NVIM_URL="https://github.com/neovim/neovim/releases/download/${NVIM_VERSION}/nvim-linux-x86_64.tar.gz"

# 一時作業用ディレクトリ作成
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Neovimのtar.gzをダウンロード
curl -LO "$NVIM_URL"

# 展開（ディレクトリ名確認用）
tar -xzf nvim-linux-x86_64.tar.gz

# 展開されたディレクトリ名に合わせて移動
# 多くの場合 "nvim-linux64" というディレクトリができる
INSTALL_DIR=$(find . -maxdepth 1 -type d -name "nvim*" | head -n 1)

# /optに移動してシステムにインストール
sudo_wrap rm -rf /opt/nvim
sudo_wrap mv "$INSTALL_DIR" /opt/nvim

# シンボリックリンク作成
sudo_wrap ln -sf /opt/nvim/bin/nvim /usr/local/bin/nvim

# 後片付け
cd ~
rm -rf "$TMP_DIR"

# 確認
echo "✅ Neovim $NVIM_VERSION installed successfully!"
nvim --version

npm install -g neovim
pip install pynvim
