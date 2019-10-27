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

# Check if zplug is installed
if [[ ! -d ~/.zplug ]]; then
  curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
fi
source ~/.zplug/init.zsh
zplug 'zplug/zplug', hook-build:'zplug --self-manage'
zplug "romkatv/powerlevel10k", as:theme, depth:1
zplug "chrissicool/zsh-256color"
zplug "mollifier/anyframe"
zplug "zsh-users/zsh-autosuggestions"
zplug "soimort/translate-shell"
zplug "plugins/git",   from:oh-my-zsh
zplug "plugins/docker-compose",   from:oh-my-zsh
zplug "plugins/docker",   from:oh-my-zsh
zplug "b4b4r07/enhancd", use:init.sh

if ! zplug check --verbose; then
  printf "Install? [y/N]: "
  if read -q; then
    echo; zplug install
  fi
fi

# Then, source plugins and add commands to $PATH
zplug load
autoload -U compinit
compinit

bindkey "^p" reverse-menu-complete
bindkey "^n" menu-complete
bindkey '^e' fbr
bindkey '^g' anyframe-widget-cd-ghq-repository
bindkey '^b' anyframe-widget-cdr
bindkey '^x^i' anyframe-widget-insert-git-branch
bindkey '^x^f' anyframe-widget-insert-filename
bindkey -v

zstyle ':completion:*:default' menu select=1

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
if [ $(uname) = "Darwin" ]; then
    alias ll='ls -GalF'
    alias la='ls -GA'
    alias l='ls -GCF'
elif [ $(uname) = "Linux" ]; then
    alias ll='ls -alF --color'
    alias la='ls -A --color'
    alias l='ls -CF --color'
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi
alias tma='tmux a -t '
alias dps='docker ps'
alias dim='docker images'
alias drm='docker rm $(docker ps -aqf "status=exited") 2> /dev/null'
alias drmi='docker rmi $(docker images -aqf "dangling=true") 2> /dev/null'
alias dc='docker-compose'
tmn() { tmux new-session -s $1 -n $1 }
de () { docker exec -it $1 /bin/bash  }
dceb () { docker-compose exec $1 /bin/bash  }
tm() {
  [[ -n "$TMUX" ]] && change="switch-client" || change="attach-session"
  if [ $1 ]; then
    tmux $change -t "$1" 2>/dev/null || (tmux new-session -d -s $1 && tmux $change -t "$1"); return
  fi
  session=$(tmux list-sessions -F "#{session_name}" 2>/dev/null | fzf-tmux --exit-0) &&  tmux $change -t "$session" || echo "No sessions found."
}

if [[ -x "`which lab`" ]]; then
  alias git='lab' && compdef git=lab
  fpath=(~/.config/lab/_lab $fpath)
  fpath=(~/.config/lab $fpath)
fi

[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"

fpath=($HOME/.zsh/anyframe(N-/) $fpath)
autoload -Uz anyframe-init
anyframe-init

# fbr - checkout git branch (including remote branches)
fbr() {
  local branches branch
  branches=$(git branch --all | grep -v HEAD) &&
  branch=$(echo "$branches" |
           fzf-tmux -d $(( 2 + $(wc -l <<< "$branches") )) +m) &&
  git checkout $(echo "$branch" | sed "s/.* //" | sed "s#remotes/[^/]*/##")
}
zle -N fbr

autoload -Uz chpwd_recent_dirs cdr add-zsh-hook
add-zsh-hook chpwd chpwd_recent_dirs

zstyle ":anyframe:selector:fzf-tmux:" command 'fzf-tmux --extended'
zstyle ":anyframe:selector:fzf:" command 'fzf --extended'

# DO NOT EDIT HERE
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# DO NOT EDIT END

# fd - including hidden directories
fd() {
  local dir
  dir=$(find ${1:-.} -type d 2> /dev/null | fzf-tmux +m) && cd "$dir"
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

eval "$(direnv hook zsh)"
function gi() { curl -L -s https://www.gitignore.io/api/$@ ;}

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
