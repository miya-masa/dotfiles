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

export LANG=ja_JP.UTF-8
export LC_TIME=C
export LC_MESSAGES=C
export PAGER=less
export EDITOR=nvim
export TERM=screen-256color

###
### history
###
HISTFILE=~/.zsh_history
HISTSIZE=500000
SAVEHIST=500000

# Check if zinit is installed
if [[ ! -d ~/.zinit ]]; then
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/zdharma/zinit/master/doc/install.sh)"
fi
source ~/.zinit/bin/zinit.zsh
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit
autoload -Uz compinit
compinit

# Load OMZ Git library
zinit snippet OMZL::git.zsh

# Load Git plugin from OMZ
zinit snippet OMZP::git
zinit cdclear -q # <- forget completions provided up to this moment

setopt promptsubst

# Load theme from OMZ
zinit snippet OMZT::gnzh

# Load normal GitHub plugin with theme depending on OMZ Git library
zinit light "dracula/zsh"

zinit wait lucid light-mode for \
  atinit"zicompinit; zicdreplay" \
      zdharma/fast-syntax-highlighting \
  atload"_zsh_autosuggest_start" \
      zsh-users/zsh-autosuggestions \
  blockf atpull'zinit creinstall -q .' \
      zsh-users/zsh-completions

zinit ice depth=1; zinit light romkatv/powerlevel10k

zinit light "soimort/translate-shell"

zinit light "mollifier/anyframe"
fpath=($HOME/.zsh/anyframe(N-/) $fpath)
autoload -Uz anyframe-init
anyframe-init

bindkey "^p" reverse-menu-complete
bindkey "^n" menu-complete
bindkey '^e' anyframe-widget-checkout-git-branch
bindkey '^g' anyframe-widget-cd-ghq-repository
bindkey '^b' anyframe-widget-cdr
bindkey '^x^i' anyframe-widget-insert-git-branch
bindkey '^x^f' anyframe-widget-insert-filename
bindkey -v

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
alias drm='docker rm $(docker ps -aqf "status=exited") 2> /dev/null'
alias drmi='docker rmi $(docker images -aqf "dangling=true") 2> /dev/null'
alias dc='docker-compose'
tmn() {
  if type "autojump" > /dev/null 2>&1; then
    j $1
  fi
  tmux new-session -s $1 -n $1
}
de () { docker exec -it $1 /bin/bash  }
dceb () { docker-compose exec $1 /bin/bash  }
jwt-show () { echo $1 | jwt -show - }
tm() {
  [[ -n "$TMUX" ]] && change="switch-client" || change="attach-session"
  if [ $1 ]; then
    tmux $change -t "$1" 2>/dev/null || (tmux new-session -d -s $1 && tmux $change -t "$1"); return
  fi
  session=$(tmux list-sessions -F "#{session_name}" 2>/dev/null | fzf --exit-0) &&  tmux $change -t "$session" || echo "No sessions found."
}

if [[ -x "`which lab`" ]]; then
  fpath=(~/.config/lab/_lab $fpath)
  fpath=(~/.config/lab $fpath)
fi

# fbr - checkout git branch (including remote branches)
fbr() {
  local branches branch
  branches=$(git branch --all | grep -v HEAD) &&
  branch=$(echo "$branches" |
           fzf -d $(( 2 + $(wc -l <<< "$branches") )) +m) &&
  git checkout $(echo "$branch" | sed "s/.* //" | sed "s#remotes/[^/]*/##")
}
zle -N fbr

# DO NOT EDIT HERE
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# DO NOT EDIT END

# fd - including hidden directories
fd() {
  local dir
  dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) && cd "$dir"
}

# # options
set -o auto_list
set -o auto_menu
set -o auto_cd
set -o list_packed
set -o no_beep
set -o no_nomatch
set -o prompt_subst
set -o transient_rprompt
set -o hist_ignore_dups
set -o hist_ignore_all_dups
set -o hist_reduce_blanks
set -o hist_no_store
set -o hist_verify
set -o share_history
set -o extended_history
set -o append_history
set -o auto_pushd
set -o list_packed
set -o list_types
set -o no_flow_control
set -o print_eight_bit
set -o pushd_ignore_dups
set -o rec_exact
set -o autoremoveslash
unset list_beep
set -o glob
set -o glob_complete
set -o complete_in_word
set -o numeric_glob_sort
set -o mark_dirs
set -o magic_equal_subst
set -o always_last_prompt
set -o interactivecomments

autoload -U +X bashcompinit && bashcompinit
if [ $(uname) = "Darwin" ]; then
   . ~/.zshrc_darwin
elif [ $(uname) = "Linux" ]; then
   . ~/.zshrc_linux
fi
[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"

eval "$(direnv hook zsh)"
function gi() { curl -L -s https://www.gitignore.io/api/$@ ;}

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
export PATH="/home/linuxbrew/.linuxbrew/opt/node@10/bin:$PATH"

export PATH="/usr/local/opt/gettext/bin:$PATH"
### End of Zinit's installer chunk
#
#
if [[ -x "`which kubectl`" ]]; then
  source <(kubectl completion zsh)
fi

if [[ -x "`which minikube`" ]]; then
  source <(minikube completion zsh)
fi

if [[ -x "`which jira`" ]]; then
  eval "$(jira --completion-script-bash)"
fi

[[ ! -f ~/.cargo/env ]] || source ~/.cargo/env

export PATH="$HOME/.poetry/bin:$PATH"

export PATH="$HOME/.rbenv/bin:$PATH"
[[ ! -f ~/.rbenv/rbenv ]] || eval "$(rbenv init - zsh)"

export PATH="$HOME/.local/bin:$PATH"

eval "$(pyenv init -)"
