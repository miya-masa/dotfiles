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
  git clone https://github.com/zplug/zplug ~/.zplug
  source ~/.zplug/init.zsh && zplug update --self
fi
source ~/.zplug/init.zsh
zplug 'zplug/zplug', hook-build:'zplug --self-manage'
zplug "mafredri/zsh-async"
zplug "sindresorhus/pure", use:pure.zsh, from:github, as:theme
zplug "zsh-users/zsh-syntax-highlighting"
zplug "zsh-users/zsh-history-substring-search"
zplug "zsh-users/zsh-autosuggestions"
zplug "zsh-users/zsh-completions"
zplug 'zsh-users/zaw'
zplug "chrissicool/zsh-256color"
zplug "mollifier/anyframe"
zplug "mollifier/cd-gitroot"
zplug "soimort/translate-shell"
zplug "zsh-users/zsh-history-substring-search", hook-build:"__zsh_version 4.3"
zplug "plugins/git",   from:oh-my-zsh
zplug "plugins/docker-compose",   from:oh-my-zsh
zplug "plugins/docker",   from:oh-my-zsh
zplug "junegunn/fzf-bin", as:command, from:gh-r, rename-to:fzf
zplug "junegunn/fzf", as:command, use:bin/fzf-tmu
zplug "jocelynmallon/zshmarks"
# zplug "b4b4r07/enhancd", use:init.sh

if ! zplug check --verbose; then
  printf "Install? [y/N]: "
  if read -q; then
    echo; zplug install
  fi
fi

autoload -Uz chpwd_recent_dirs cdr add-zsh-hook is-at-least
if is-at-least 4.3.10; then
add-zsh-hook chpwd chpwd_recent_dirs
zstyle ':chpwd:*' recent-dirs-max 5000
zstyle ':chpwd:*' recent-dirs-default yes
fi

# Then, source plugins and add commands to $PATH
zplug load
autoload -U compinit
compinit

bindkey "^p" reverse-menu-complete
bindkey "^n" menu-complete

zstyle ':completion:*:default' menu select=1

bindkey -v


# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

# colored GCC warnings and errors
#export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# some more ls aliases
alias ll='ls -GalF'
alias la='ls -GA'
alias l='ls -GCF'

# move directories
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias datef='date -j -f "%Y%m%d%H%M%S" "+%s"'
# tm - create new tmux session, or switch to existing one. Works from within tmux too. (@bag-man)
# `tm` will allow you to select your tmux session via fzf.
# `tm irc` will attach to the irc session (if it exists), else it will create it.

tm() {
  [[ -n "$TMUX" ]] && change="switch-client" || change="attach-session"
  if [ $1 ]; then
    tmux $change -t "$1" 2>/dev/null || (tmux new-session -d -s $1 && tmux $change -t "$1"); return
  fi
  session=$(tmux list-sessions -F "#{session_name}" 2>/dev/null | fzf --exit-0) &&  tmux $change -t "$session" || echo "No sessions found."
}

alias tma='tmux a -t '
alias git='lab'

[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"

eval "$(fasd --init auto)"

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
bindkey '^e' fbr
bindkey '^g' anyframe-widget-cd-ghq-repository
bindkey '^b' anyframe-widget-cdr
bindkey '^x^i' anyframe-widget-insert-git-branch
bindkey '^x^f' anyframe-widget-insert-filename

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
  dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) && cd "$dir"
}

# Install (one or multiple) selected application(s)
# using "brew search" as source input
# mnemonic [B]rew [I]nstall [P]lugin
bip() {
  local inst=$(brew search | fzf -m)

  if [[ $inst ]]; then
    for prog in $(echo $inst);
    do; brew install $prog; done;
  fi
}

v() {
  local file
  file="$(fasd -Rfl "$1" | fzf -1 -0 --no-sort +m)" && vi "${file}" || return 1
}

## options
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

eval "$(direnv hook zsh)"
function gi() { curl -L -s https://www.gitignore.io/api/$@ ;}

alias dps='docker ps'
alias dim='docker images'
alias drm='docker rm $(docker ps -aqf "status=exited") 2> /dev/null'
alias drmi='docker rmi $(docker images -aqf "dangling=true") 2> /dev/null'
alias dc='docker-compose'

# Load rbenv automatically by appending
# the following to ~/.zshrc:

eval "$(rbenv init -)"
fpath=(~/.config/lab/_lab $fpath)
fpath=(~/.config/lab $fpath)

#### functions
#

# dcrm () { docker-compose stop $1 && docker-compose rm -f $1 }
tmn() { tmux new-session -s $1 -n $1 }
de () { docker exec -it $1 /bin/bash  }
dceb () { docker-compose exec $1 /bin/bash  }

