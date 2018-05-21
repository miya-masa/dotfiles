# Setup fzf
# ---------
if [[ ! "$PATH" == */Users/miyauchi-masayuki/.fzf/bin* ]]; then
  export PATH="$PATH:/Users/miyauchi-masayuki/.fzf/bin"
fi

# Auto-completion
# ---------------
[[ $- == *i* ]] && source "/Users/miyauchi-masayuki/.fzf/shell/completion.zsh" 2> /dev/null

# Key bindings
# ------------
source "/Users/miyauchi-masayuki/.fzf/shell/key-bindings.zsh"

source ~/.fzfadd.zsh
