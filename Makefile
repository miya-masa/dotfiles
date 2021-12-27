install:
	./install.sh

deploy: $(HOME)/.config $(HOME)/.vim
	./install.sh deploy
