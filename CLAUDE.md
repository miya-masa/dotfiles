# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Initial Setup

```bash
# Full setup from scratch (on a new machine)
apt update && apt install -y curl sudo git
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply miya-masa
```

### Daily Operations

```bash
chezmoi update    # Pull latest changes and apply
chezmoi apply     # Apply changes from source state
chezmoi diff      # Preview changes before applying
chezmoi edit      # Edit source files (opens in $EDITOR)
```

### Package Management

```bash
brew bundle --file=Brewfile_mac     # macOS packages
brew bundle --file=Brewfile_linux   # Linux packages
mise install                         # Install all language versions
```

## Architecture Overview

This is a **chezmoi-managed dotfiles repository** for Unix/Linux development environments.

### Chezmoi File Naming Convention

Chezmoi uses special prefixes to manage dotfiles:

- `dot_` → `.` (e.g., `dot_zshrc` becomes `.zshrc`)
- `dot_config/` → `.config/`
- `.chezmoiscripts/` → Auto-executed installation scripts

### Installation Scripts

Located in `.chezmoiscripts/`, executed in order by filename:

- `01-install-apt-packages.sh.tmpl` - System packages (Linux only)
- `02-install-homebrew.sh.tmpl` - Homebrew setup
- `03-install-mise.sh.tmpl` - Language version manager
- `04-generate-ssh-keys.sh.tmpl` - SSH key generation (RSA, ECDSA, ED25519)
- `10-install-neovim.sh.tmpl` - Latest Neovim from GitHub releases
- `11-install-docker.sh.tmpl` - Docker rootless setup
- `12-install-tpm.sh.tmpl` - Tmux plugin manager
- `13-install-1password.sh.tmpl` - 1Password CLI
- `30-install-go-tools.sh.tmpl` - Go development tools
- `31-install-python-packages.sh.tmpl` - Python packages
- `32-install-npm-packages.sh.tmpl` - npm global packages
- `99-setup-shell.sh.tmpl` - Set zsh as default shell

### Core Components

**Shell**: Zsh with Zinit plugin manager, platform-specific configs (`dot_zshrc_darwin`, `dot_zshrc_linux`)

**Editor**: Neovim with LazyVim framework (`dot_config/nvim/lua/plugins/` for custom plugins)

**Terminal**: Tmux with TPM, WezTerm/Alacritty with Catppuccin theme

**Languages**: mise manages versions (Go, Node, Python, Lua, Zig, etc. - see `dot_mise.toml`)

### Key Bindings

- **Tmux prefix**: `Ctrl+s` (not default `Ctrl+b`)
- **Tmux split**: `|` (vertical), `-` (horizontal)
- **Neovim leader**: `,`

### Platform Differences

Templates (`.tmpl` files) use Go templating with `{{ if eq .chezmoi.os "linux" }}` for platform-specific logic. Separate Brewfiles exist for macOS (`Brewfile_mac`) and Linux (`Brewfile_linux`).

