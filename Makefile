all: git tmux zsh nvim fzf

tmux:
	mkdir -p ${HOME}/.tmux
	ln -fsn ${PWD}/.tmux/new-session ${HOME}/.tmux/new-session
	ln -fs ${PWD}/.tmux.conf ${HOME}/.tmux.conf

zsh:
	ln -fs ${PWD}/.zshrc ${HOME}/.zshrc
	ln -fs ${PWD}/.zprofile ${HOME}/.zprofile

nvim:
	mkdir -p ${HOME}/.config
	ln -fsn ${PWD}/.config ${HOME}/.config

git:
	ln -fs ${PWD}/.gitconfig ${HOME}/.gitconfig

fzf:
	${PWD}/init_fzf.sh
	ln -fs ${PWD}/.fzfadd.zsh ${HOME}/.fzfadd.zsh
