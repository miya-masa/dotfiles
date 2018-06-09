export GOPATH="$HOME/go"
export PATH=$GOPATH/bin:$PATH
export XDG_CONFIG_HOME=$HOME/.config
export TERM="xterm-256color"
autoload -Uz compinit colors
compinit
colors

[ -f ~/.local_zprofile ] && source ~/.local_zprofile
