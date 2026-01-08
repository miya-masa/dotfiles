# dotfiles

chezmoi-managed dotfiles for Unix/Linux development environments.

## Quick Start

### New Machine Setup

```bash
apt update && apt install -y curl sudo git
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply miya-masa
```

### macOS

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply miya-masa
```

## Daily Operations

```bash
chezmoi update    # Pull latest changes and apply
chezmoi apply     # Apply changes from source state
chezmoi diff      # Preview changes before applying
chezmoi edit      # Edit source files
```

## What's Included

- **Shell**: Zsh with Zinit plugin manager
- **Editor**: Neovim with LazyVim
- **Terminal**: Tmux (prefix: `Ctrl+s`), WezTerm, Alacritty
- **Languages**: mise (Go, Node, Python, etc.)
- **Tools**: fzf, ripgrep, lazygit, lazydocker, ghq, delta

## Platform Support

- Linux (Ubuntu/Debian)
- macOS
