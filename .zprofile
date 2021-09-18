export GOPATH="$HOME/go"
export PATH=$GOPATH/bin:$PATH:/usr/local/go/bin
export XDG_CONFIG_HOME=$HOME/.config
export PATH=/home/linuxbrew/.linuxbrew/bin:$PATH
export PATH=/home/linuxbrew/.linuxbrew/sbin:$PATH
export PATH=${PATH}:${HOME}/bin
export TERM="xterm-256color"
autoload -Uz compinit colors
compinit
colors

[ -f ~/.zprofile.local ] && source ~/.zprofile.local
[ -f /home/linuxbrew/.linuxbrew/bin/brew ] && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
[ -f ~/.gvm/scripts/gvm ] && source ~/.gvm/scripts/gvm && gvm use master
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
if [[ -x "`which pyenv`" ]]; then
  export PATH="$(pyenv root)/shims:$PATH"
  eval "$(pyenv init -)"
fi
