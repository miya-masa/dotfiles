$(HOME)/.config:
	mkdir -p ${HOME}/.config

install:
	brew bundle

deploy: $(HOME)/.config
	mkdir -p ${HOME}/.config/lab
	ln -fs ${PWD}/.config/lab/_lab ${HOME}/.config/lab/_lab
	mkdir -p ${HOME}/.tmux
	ln -fsn ${PWD}/.tmux/tmuxline.conf ${HOME}/.tmux/tmuxline.conf
	ln -fs ${PWD}/.tmux.conf ${HOME}/.tmux.conf
	ln -fs ${PWD}/.zshrc ${HOME}/.zshrc
	ln -fs ${PWD}/.p10k.zsh ${HOME}/.p10k.zsh
	ln -fs ${PWD}/.zprofile ${HOME}/.zprofile
	ln -fs ${PWD}/.config/nvim ${HOME}/.config/nvim
	ln -fs ${PWD}/.gitconfig ${HOME}/.gitconfig
