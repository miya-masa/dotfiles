# dotfiles

## package manager(linux or macos)
`./install.sh brew`

## Software

* zplug `./install.sh zplug`
* neovim
* Silver Searcher `./install.sh ag`
* jq `./install.sh jq`
* nerd-fonts `./install.sh font`
  ```
   https://github.com/ryanoasis/nerd-fonts#font-installation
  ```
* Universal Ctags
  ```
  sudo apt-get install autoconf automake libtool autoconf-doc libtool-doc```
  ```
* https://github.com/soimort/translate-shell
* tmux `./install.sh tmux`
  * tmuxinator
* tmux-git
* https://github.com/thewtex/tmux-mem-cpu-load
* https://github.com/tmux-plugins/tpm
  ```
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
  ```
* flake8
  * `pip install flake8`
* yapf
  * `pip install yapf`

* LSP
  * go get -u github.com/sourcegraph/go-langserver 

* direnv
  * https://direnv.net/

## nvim settings(Mac or Ubuntu)

1. Clone this repository
1. make all
1. nvim
1. UpdateRemotePlugin
1. GoInstallBinary(for golang)
1. PlugInstall
1. restart nvim

## other recommended

* https://github.com/mhinz/neovim-remote
