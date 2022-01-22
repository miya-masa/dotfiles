# Setup fzf
# ---------
if [[ ! "$PATH" == */home/masayuki/.fzf/bin* ]]; then
  export PATH="${PATH:+${PATH}:}/home/masayuki/.fzf/bin"
fi

# Auto-completion
# ---------------
[[ $- == *i* ]] && source "/home/masayuki/.fzf/shell/completion.zsh" 2> /dev/null

# Key bindings
# ------------
source "/home/masayuki/.fzf/shell/key-bindings.zsh"
