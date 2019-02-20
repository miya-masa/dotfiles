gvm:
	curl -s -S -L https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer | bash
	source ${HOME}/.gvm/scripts/gvm

go:
	 gvm install master

$(HOME)/.config:
	mkdir -p ${HOME}/.config

tmuxinator: $(HOME)/.config
	ln -fs ${PWD}/.config/tmuxinator ${HOME}/.config/tmuxinator

tmux:
	mkdir -p ${HOME}/.tmux
	ln -fsn ${PWD}/.tmux/tmuxline.conf ${HOME}/.tmux/tmuxline.conf
	ln -fs ${PWD}/.tmux.conf ${HOME}/.tmux.conf

zsh:
	ln -fs ${PWD}/.zshrc ${HOME}/.zshrc
	ln -fs ${PWD}/.zprofile ${HOME}/.zprofile

nvim: $(HOME)/.config
	mkdir -p ${HOME}/.config
	ln -fs ${PWD}/.config/nvim ${HOME}/.config/nvim

git:
	ln -fs ${PWD}/.gitconfig ${HOME}/.gitconfig

fzf:
	${PWD}/init_fzf.sh

fish-mac:
	brew install fish
	curl https://git.io/fisher --create-dirs -sLo ~/.config/fish/functions/fisher.fish

ranger:
	pip install ranger-fm

pip3:
	brew install python
