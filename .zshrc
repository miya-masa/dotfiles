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

export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
export PAGER=less
export EDITOR=nvim
export VISUAL="nvim"
export TERM=screen-256color

export XDG_CONFIG_HOME=$HOME/.config
[ -f /home/linuxbrew/.linuxbrew/bin/brew ] && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
export PATH=${PATH}:${HOME}/bin
[ -f ~/.zprofile.local ] && source ~/.zprofile.local
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.poetry/bin:$PATH"
export PATH="$HOME/.rbenv/bin:$PATH"
export PATH="/usr/local/opt/gettext/bin:$PATH"
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
export FZF_DEFAULT_OPTS='--layout reverse --height=30%'


###
### history
###
HISTFILE=~/.zsh_history
HISTSIZE=500000
SAVEHIST=500000

### Added by Zinit's installer
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
    print -P "%F{33} %F{220}Installing %F{33}ZDHARMA-CONTINUUM%F{220} Initiative Plugin Manager (%F{33}zdharma-continuum/zinit%F{220})…%f"
    command mkdir -p "$HOME/.local/share/zinit" && command chmod g-rwX "$HOME/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "$HOME/.local/share/zinit/zinit.git" && \
        print -P "%F{33} %F{34}Installation successful.%f%b" || \
        print -P "%F{160} The clone has failed.%f%b"
fi

source "$HOME/.local/share/zinit/zinit.git/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

## plugins

zinit light zsh-users/zsh-completions
zinit light zsh-users/zsh-autosuggestions

### docker(completion)
zinit snippet https://raw.githubusercontent.com/docker/cli/master/contrib/completion/zsh/_docker
zinit snippet https://raw.githubusercontent.com/docker/compose/1.29.2/contrib/completion/zsh/_docker-compose

### zsh-syntax-highlighting
zinit light "zsh-users/zsh-syntax-highlighting"

# fbr - checkout git branch (including remote branches)
fbr() {
  zle -I             # キー入力のバッファをクリア
  local branches branch
  branches=$(git branch --all --sort=-authordate | grep -v HEAD)
  branch=$(echo "$branches" | fzf -d $(( 2 + $(wc -l <<< "$branches") )) +m)
  if [[ $branch = '' ]]; then
    return
  fi
  local checkout_branch=$(echo "$branch" | sed "s/.* //" | sed "s#remotes/[^/]*/##")

  # redisplay the command line

  BUFFER="git checkout $checkout_branch"
  zle accept-line
  zle reset-prompt
}
zle -N fbr

__cd-git(){
  zle -I             # キー入力のバッファをクリア
  local repo=$(ghq list | fzf)
  if [ -z "$repo" ]; then
    return
  fi
  cd "$(ghq root)/$repo"
  # redisplay the command line
  BUFFER="cd \"$(ghq root)/$repo\""  # cdコマンドをBUFFERに代入
  zle accept-line
  zle reset-prompt
}
zle -N cd-git __cd-git

# fh - repeat history
__fh() {
  local cmd=$( ([ -n "$ZSH_NAME" ] && fc -l 1 || history) | fzf +s --tac | sed -E 's/ *[0-9]*\*? *//' | sed -E 's/\\/\\\\/g')
  LBUFFER+="$cmd"
  CURSOR=$#LBUFFER
  # redisplay the command line
  zle -R -c
}
zle -N fh __fh

if [[ -x "`which glab`" ]] ; then
  __insert-issue-id() {
    local issue_number_row=$(glab ls | tail -n +3 | fzf)
    if [ -z "$issue_number_row" ]; then
      return
    fi
    local issue_number=$(echo $issue_number_row | awk '{print $1}')
    LBUFFER+="feature/${issue_number}_"
    CURSOR=$#LBUFFER
    # redisplay the command line
    zle -R -c
  }
  zle -N insert-issue-id __insert-issue-id
fi


### reset bind key
bindkey -d
bindkey -v
bindkey "^N" down-line-or-history
bindkey "^P" up-line-or-history
bindkey '^e^e' fbr
bindkey '^g' cd-git
bindkey '^r' fh
bindkey '^x^b' insert-issue-id

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
alias dps='docker ps'
alias dim='docker images'
alias dkill='docker container ls -q | xargs docker kill'
alias dc='docker compose'
alias rand="head -n 10 /dev/urandom | base64 | head -n 1 | cut -c 1-32 | tr '/+' '_-'"
alias tagsort="git tag | tr - \~ | sort -V | tr \~ -"

# DO NOT EDIT HERE
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# Open in tmux popup if on tmux, otherwise use --height mode
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

### End of Zinit's installer chunk

if [[ -x "`which jira`" ]]; then
  jira completion zsh > ~/.local/share/zinit/completions/_jira
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

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"
if [[ -x "`which op`" ]]; then
  eval "$(op completion zsh)"; compdef _op op
fi

# complete -o nospace -C /home/linuxbrew/.linuxbrew/Cellar/terraform/1.2.4/bin/terraform terraform
# complete -o nospace -C /home/linuxbrew/.linuxbrew/Cellar/vault/1.3.2/bin/vault vault
[ -s "$HOME/.local/bin/mise" ] && eval "$(~/.local/bin/mise activate zsh)"

# Load a few important annexes, without Turbo
# (this is currently required for annexes)
zinit light-mode for \
    zdharma-continuum/zinit-annex-as-monitor \
    zdharma-continuum/zinit-annex-bin-gem-node \
    zdharma-continuum/zinit-annex-patch-dl \
    zdharma-continuum/zinit-annex-rust

### End of Zinit's installer chunk

j() {
    local preview_cmd="ls {2..}"
    if command -v exa &> /dev/null; then
        preview_cmd="exa -l {2}"
    fi

    if [[ $# -eq 0 ]]; then
                 cd "$(autojump -s | sort -k1gr | awk -F : '$1 ~ /[0-9]/ && $2 ~ /^\s*\// {print $1 $2}' | fzf --height 40% --reverse --inline-info --preview "$preview_cmd" --preview-window down:50% | cut -d$'\t' -f2- | sed 's/^\s*//')"
    else
        cd $(autojump $@)
    fi
}

cd() {
    if [[ "$#" != 0 ]]; then
        builtin cd "$@";
        return
    fi
    local dir
    dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) &&
 cd "$dir"
}

# Use fd and fzf to get the args to a command.
# Works only with zsh
# Examples:
# f mv # To move files. You can write the destination after selecting the files.
# f 'echo Selected:'
# f 'echo Selected music:' --extension mp3
# fm rm # To rm files in current directory
f() {
    sels=( "${(@f)$(fd "${fd_default[@]}" "${@:2}"| fzf)}" )
    test -n "$sels" && print -z -- "$1 ${sels[@]:q:q}"
}

# Like f, but not recursive.
fm() f "$@" --max-depth 1

# Deps
alias fz="fzf-noempty --bind 'tab:toggle,shift-tab:toggle+beginning-of-line+kill-line,ctrl-j:toggle+beginning-of-line+kill-line,ctrl-t:top' --color=light -1 -m"
fzf-noempty () {
	local in="$(</dev/stdin)"
	test -z "$in" && (
		exit 130
	) || {
		ec "$in" | fzf "$@"
	}
}
ec () {
	if [[ -n $ZSH_VERSION ]]
	then
		print -r -- "$@"
	else
		echo -E -- "$@"
	fi
}

# Usage: rgf [<rg SYNOPSIS>]
function rgf {
# 1. Search for text in files using Ripgrep
# 2. Interactively narrow down the list using fzf
# 3. Open the file in Vim
rg --color=always --line-number --no-heading --smart-case "${*:-}" |
  fzf --ansi \
      --color "hl:-1:underline,hl+:-1:underline:reverse" \
      --delimiter : \
      --preview 'bat --color=always {1} --highlight-line {2}' \
      --bind 'enter:become(vim {1} +{2})'
}

# zsh; needs setopt re_match_pcre. You can, of course, adapt it to your own shell easily.
tmuxkillf () {
    local sessions
    sessions="$(tmux ls|fzf --exit-0 --multi)"  || return $?
    local i
    for i in "${(f@)sessions}"
    do
        [[ $i =~ '([^:]*):.*' ]] && {
            echo "Killing $match[1]"
            tmux kill-session -t "$match[1]"
        }
    done
}

# tm - create new tmux session, or switch to existing one. Works from within tmux too. (@bag-man)
# `tm` will allow you to select your tmux session via fzf.
# `tm irc` will attach to the irc session (if it exists), else it will create it.

tm() {
  [[ -n "$TMUX" ]] && change="switch-client" || change="attach-session"
  if [ $1 ]; then
    tmux $change -t "$1" 2>/dev/null || (tmux new-session -d -s $1 && tmux $change -t "$1"); return
  fi
  session=$(tmux list-sessions 2>/dev/null | fzf --exit-0 | awk -F: '{ print $1 }') && tmux $change -t "$session" || echo "No sessions found."
}

pass() {
  op connect server list > /dev/null
  local result=$?

  if [ $result -ne 0 ]; then
    return
  fi

  local id=$(op item list | fzf --exit-0 | awk '{print $1}')
  if [ -z "$id" ]; then
    return
  fi
  op item get --fields label=password "$id" | xclip -selection clipboard
}


function has() {
  type "$1" >/dev/null 2>&1
}

if ! has starship; then
  curl -sS https://starship.rs/install.sh | sh
fi
eval "$(starship init zsh)"
