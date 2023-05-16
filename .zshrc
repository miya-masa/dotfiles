#  _ __ ___ (_)_   _  __ _       _ __ ___   __ _ ___  __ _( )___
# | '_ ` _ \| | | | |/ _` |_____| '_ ` _ \ / _` / __|/ _` |// __|
# | | | | | | | |_| | (_| |_____| | | | | | (_| \__ \ (_| | \__ \
# |_| |_| |_|_|\__, |\__,_|     |_| |_| |_|\__,_|___/\__,_| |___/
#              |___/
#            _
#    _______| |__  _ __ ___
#   |_  / __| '_ \| '__/ __|
#  _ / /\__ \ | | | | | (__
# (_)___|___/_| |_|_|  \___|

if [ $(uname) = "Darwin" ]; then
   . ~/.zshrc_darwin
elif [ $(uname) = "Linux" ]; then
   . ~/.zshrc_linux
fi
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
# See https://github.com/romkatv/powerlevel10k#how-do-i-initialize-direnv-when-using-instant-prompt
(( ${+commands[direnv]} )) && emulate zsh -c "$(direnv export zsh)"

if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

(( ${+commands[direnv]} )) && emulate zsh -c "$(direnv hook zsh)"

export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
export PAGER=less
export EDITOR=nvim
export TERM=screen-256color

export GOPATH="$HOME/go"
export PYENV_ROOT="$HOME/.pyenv"
export XDG_CONFIG_HOME=$HOME/.config
export PATH=$GOPATH/bin:$PATH:/usr/local/go/bin
[ -f /home/linuxbrew/.linuxbrew/bin/brew ] && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
export PATH=${PATH}:${HOME}/bin
[ -f ~/.zprofile.local ] && source ~/.zprofile.local
[ -f ~/.gvm/scripts/gvm ] && source ~/.gvm/scripts/gvm && gvm use master
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
export PATH="$PYENV_ROOT/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.poetry/bin:$PATH"
export PATH="$HOME/.rbenv/bin:$PATH"
export PATH="/usr/local/opt/gettext/bin:$PATH"
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
if [[ -x "`which pyenv`" ]]; then
  export PATH="$(pyenv root)/shims:$PATH"
  eval "$(pyenv init -)"
fi
export PATH="${PATH}:${HOME}/.local/bin/"
export PATH="/home/linuxbrew/.linuxbrew/opt/glibc/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/opt/glibc/sbin:$PATH"
if [[ -e $HOME/.krew ]]; then
  export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"
fi

[[ -s /usr/share/autojump/autojump.sh ]] && . /usr/share/autojump/autojump.sh


###
### history
###
HISTFILE=~/.zsh_history
HISTSIZE=500000
SAVEHIST=500000

# Check if zinit is installed
# init zinit
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
if [[ ! -d ${ZINIT_HOME} ]]; then
  bash -c "$(curl --fail --show-error --silent --location https://raw.githubusercontent.com/zdharma-continuum/zinit/HEAD/scripts/install.sh)"
fi
source "${ZINIT_HOME}/zinit.zsh"
autoload -Uz compinit && compinit
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

## plugins
### powerlevel10k
zinit ice depth=1; zinit light romkatv/powerlevel10k

### zsh-completions
zinit light zsh-users/zsh-completions
fpath=(path/to/zsh-completions/src $fpath)
rm -f ~/.zcompdump; compinit

### zsh-autosuggestions
zinit light zsh-users/zsh-autosuggestions

### anyframe
zinit light "mollifier/anyframe"
fpath=($HOME/.zsh/anyframe(N-/) $fpath)
autoload -Uz anyframe-init
anyframe-init

anyframe-widget-checkout-git-remote-branch() {
  anyframe-source-git-branch -n -r | grep -v HEAD | anyframe-selector-auto | awk '{print $1}' | sed "s/origin\///" | anyframe-action-execute git checkout
}
zle -N anyframe-widget-checkout-git-remote-branch

if [[ -x "`which glab`" ]] ; then
  anyframe-widget-insert-issue-branch-name() {
  issueNumber=$(glab ls | tail -n +3 | anyframe-selector-auto | awk '{print $1}')
    echo "feature/${issueNumber}"_ | anyframe-action-insert
  }
  zle -N anyframe-widget-insert-issue-branch-name
fi

anyframe-widget-git-log() {
  git log --oneline | anyframe-selector-auto |  awk '{print $1}' | anyframe-action-insert
}
zle -N anyframe-widget-git-log

### docker(completion)
zinit snippet https://raw.githubusercontent.com/docker/cli/master/contrib/completion/zsh/_docker
zinit snippet https://raw.githubusercontent.com/docker/compose/1.29.2/contrib/completion/zsh/_docker-compose

### zsh-syntax-highlighting
zinit light "zsh-users/zsh-syntax-highlighting"


### reset bind key
bindkey -d
bindkey -v
bindkey "^N" down-line-or-history
bindkey "^P" up-line-or-history
bindkey '^e^e' anyframe-widget-checkout-git-branch
bindkey '^e^r' anyframe-widget-checkout-git-remote-branch
bindkey '^g' anyframe-widget-cd-ghq-repository
bindkey '^x^i' anyframe-widget-insert-git-branch
bindkey '^f' anyframe-widget-insert-filename
bindkey '^xl' anyframe-widget-git-log
bindkey '^r' anyframe-widget-execute-history
bindkey '^x^b' anyframe-widget-insert-issue-branch-name

zstyle ':completion:*:default' menu select=1
zstyle ":anyframe:selector:" use fzf
zstyle ":anyframe:selector:fzf:" command 'fzf --height=25%'


# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# some more ls aliases
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias datef='date -j -f "%Y%m%d%H%M%S" "+%s"'
alias dps='docker ps'
alias dim='docker images'
alias dkill='docker container ls -q | xargs docker kill'
alias dc='docker compose'
alias rand="head -n 10 /dev/urandom | base64 | head -n 1 | cut -c 1-32 | tr '/+' '_-'"

pass() {
  op item get --fields label=password $(op item list | fzf --height=25% | awk '{print $1}')
}

tmn() {
  if type "autojump" > /dev/null 2>&1; then
    j $1
  fi
  tmux new-session -s $1 -n $1
}
alias ide="~/.local/bin/ide.sh"
alias tagsort="git tag | tr - \~ | sort -V | tr \~ -"

tm() {
  [[ -n "$TMUX" ]] && change="switch-client" || change="attach-session"
  if [ $1 ]; then
    tmux $change -t "$1" 2>/dev/null || (tmux new-session -d -s $1 && tmux $change -t "$1"); return
  fi
  session=$(tmux list-sessions -F "#{session_name}" 2>/dev/null | fzf --exit-0) &&  tmux $change -t "$session" || echo "No sessions found."
}

# DO NOT EDIT HERE
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# DO NOT EDIT END

# # options
# set -o auto_list
# set -o auto_menu
set -o auto_cd
set -o list_packed
set -o no_beep
set -o no_nomatch
set -o prompt_subst
# set -o transient_rprompt
set -o hist_ignore_dups
set -o hist_ignore_all_dups
set -o hist_reduce_blanks
# set -o hist_no_store
# set -o hist_verify
set -o share_history
# set -o extended_history
set -o append_history
# set -o auto_pushd
# set -o list_packed
# set -o list_types
# set -o no_flow_control
# set -o print_eight_bit
# set -o pushd_ignore_dups
# set -o rec_exact
# set -o autoremoveslash
# unset list_beep
set -o glob
set -o glob_complete
# set -o complete_in_word
# set -o numeric_glob_sort
# set -o mark_dirs
# set -o magic_equal_subst
# set -o always_last_prompt
# set -o interactivecomments

# autoload -U +X bashcompinit && bashcompinit
[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
### End of Zinit's installer chunk

if [[ -x "`which jira`" ]]; then
  jira completion zsh > "${fpath[1]}/_jira"
fi
if [[ -x "`which kubectl`" ]]; then
  source <(kubectl completion zsh)
fi

if [[ -x "`which minikube`" ]]; then
  source <(minikube completion zsh)
fi

[[ ! -f ~/.cargo/env ]] || source ~/.cargo/env
[[ ! -f ~/.rbenv/rbenv ]] || eval "$(rbenv init - zsh)"
### End of Zinit's installer chunk

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# Load a few important annexes, without Turbo
# (this is currently required for annexes)
zinit light-mode for \
    zdharma-continuum/zinit-annex-as-monitor \
    zdharma-continuum/zinit-annex-bin-gem-node \
    zdharma-continuum/zinit-annex-patch-dl \
    zdharma-continuum/zinit-annex-rust


test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"
if [[ -x "`which op`" ]]; then
  eval "$(op completion zsh)"; compdef _op op
fi

# complete -o nospace -C /home/linuxbrew/.linuxbrew/Cellar/terraform/1.2.4/bin/terraform terraform
# complete -o nospace -C /home/linuxbrew/.linuxbrew/Cellar/vault/1.3.2/bin/vault vault
