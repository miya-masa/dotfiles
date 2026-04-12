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
- `symlink_` → symlink (e.g., `dot_claude/skills/symlink_foo` creates `.claude/skills/foo` as symlink)

### Installation Scripts

Located in `.chezmoiscripts/`, prefixed with `run_onchange_after_` and executed in order by number:

- `01` - apt packages (Linux only)
- `02` - Homebrew
- `03` - mise (language version manager)
- `04` - SSH key generation
- `10` - Neovim (from GitHub releases)
- `11` - Docker (rootless)
- `12` - TPM (Tmux plugin manager)
- `13` - 1Password CLI
- `14` - opencode
- `15` - Claude Code
- `16` - beads (git-backed issue tracker)
- `30` - Go tools
- `31` - Python packages
- `32` - npm packages
- `33` - Claude skills
- `99` - Set zsh as default shell

### Core Components

**Shell**: Zsh with Zinit plugin manager, platform-specific configs (`dot_zshrc_darwin`, `dot_zshrc_linux`). Custom fzf-powered functions: `fbr` (git branch switch), `cd-git` (ghq repo jump), `sshf` (SSH host picker), `tm` (tmux session picker).

**Editor**: Neovim with LazyVim framework (`dot_config/nvim/lua/plugins/` for custom plugins). LazyVim extras are configured in `dot_config/nvim/lazyvim.json`.

**Terminal**: Tmux with TPM, WezTerm/Ghostty/Alacritty with Catppuccin theme

**Languages**: mise manages versions (Go, Node, Python, Lua, Zig, etc. - see `dot_mise.toml`)

**Claude Code**: Custom skills (`dot_claude/skills/`), agents (`dot_claude/agents/`), and settings (`dot_claude/settings.json`) are chezmoi-managed.

### Key Bindings

- **Tmux prefix**: `Ctrl+s` (not default `Ctrl+b`)
- **Tmux split**: `|` (vertical), `-` (horizontal)
- **Neovim leader**: `,`
- **Zsh**: `Ctrl+e Ctrl+e` (git branch), `Ctrl+g` (ghq cd), `Ctrl+r` (history)

### Platform Differences

Templates (`.tmpl` files) use Go templating with `{{ if eq .chezmoi.os "linux" }}` for platform-specific logic. Separate Brewfiles exist for macOS (`Brewfile_mac`) and Linux (`Brewfile_linux`).

### Git Branch Strategy

This repo uses a public/private split. `master` branch pushes to `origin` (private), `master-upstream` pushes to `upstream` (public). When making changes, consider whether they contain private information before syncing to upstream.

