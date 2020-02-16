$(HOME)/.config:
	mkdir -p ${HOME}/.config

$(HOME)/.vim:
	mkdir -p $(HOME)/.vim

install:
	brew bundle

install_linux:
	./install_linux.sh

deploy: $(HOME)/.config $(HOME)/.vim
	mkdir -p ${HOME}/.config/lab
	ln -fs ${PWD}/.config/lab/_lab ${HOME}/.config/lab/_lab
	mkdir -p ${HOME}/.tmux
	ln -fs ${PWD}/.tmux/tmuxline.conf ${HOME}/.tmux/tmuxline.conf
	ln -fs ${PWD}/.tmux.conf ${HOME}/.tmux.conf
	ln -fs ${PWD}/.zshrc ${HOME}/.zshrc
	ln -fs ${PWD}/.zshrc_linux ${HOME}/.zshrc_linux
	ln -fs ${PWD}/.zshrc_darwin ${HOME}/.zshrc_darwin
	ln -fs ${PWD}/.p10k.zsh ${HOME}/.p10k.zsh
	ln -fs ${PWD}/.zprofile ${HOME}/.zprofile
	ln -fs ${PWD}/.gitconfig ${HOME}/.gitconfig
	ln -fs ${PWD}/.vim/vimrcs ${HOME}/.vim
	ln -Fs ${PWD}/.config/nvim ${HOME}/.config
