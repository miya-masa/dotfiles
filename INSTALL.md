# Ubuntu
## install applications

```
# install basic software
sudo apt -y install software-properties-common
sudo add-apt-repository ppa:hnakamur/universal-ctags
sudo apt update
sudo apt install -y zsh curl git build-essential dconf-cli \
    gcc make \
    pkg-config autoconf automake \
    python3-docutils \
    libseccomp-dev \
    libjansson-dev \
    libyaml-dev \
    libxml2-dev \
    software-properties-common \
    universal-ctags \
    tmux \
    linuxbrew-wrapper \
    zsh \
    vlc \
    xsel
ssh-keygen -t rsa -N {PASSWORD}
cat ~/.ssh/id_rsa/pub
# registered ssh key
chsh -s $(which zsh)
zsh

# docker install
curl -fsSL https://get.docker.com -o get-docker.sh
echo "$password" | sudo -S sh get-docker.sh
rm get-docker.sh

git clone git@github.com:miya-masa/dotfiles.git
cd dotfiles
brew bundle
go get github.com/motemen/ghq

# deploy configurations
make nvim git tmux zsh
# startify vim
mkdir -p ~/.vim/files/info

# modified input method
# input method on -> hennkann
# input method off -> muhennkann

# zplug installation is automatic.
# but need zplug load

# input method
sudo apt -y install fcitx-mozc
im-config -n fcitx

# modified input method
# input method on -> hennkann
# input method off -> muhennkann


# install mackbuntu macbuntu
sudo add-apt-repository ppa:noobslab/macbuntu && \
sudo apt update && \

sudo apt install -y macbuntu-os-icons-v1804
sudo apt install -y macbuntu-os-ithemes-v1804
sudo apt install -y slingscold albert plank
sudo apt install -y macbuntu-os-plank-theme-v1804
sudo apt install -y gnome-tweak-tool

wget -O mac-fonts.zip http://drive.noobslab.com/data/Mac/macfonts.zip && \
sudo unzip mac-fonts.zip -d /usr/share/fonts; rm mac-fonts.zip && \
sudo fc-cache -f -v

# install font
git clone git@github.com:miiton/Cica.git
cd Cica
# output to ./dist/
docker-compose build ; docker-compose run --rm cica
sudo cp ./dist/Cica* /usr/share/fonts
cd ../
rm -rf Cica
sudo fc-cache -f -v

# tmux battery
sudo apt install -y acpi

# tmux plugin
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
# exexudte prefix I in tmux

# yarnのインストール
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update && sudo apt -y install yarn

# rangerのインストール

```
