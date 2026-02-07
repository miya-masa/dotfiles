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

## Public / Private Repository Split

Manage public and private configs from a single worktree by assigning each branch a different remote.

| Branch            | Remote              | Purpose                               |
| ----------------- | ------------------- | ------------------------------------- |
| `master`          | `origin` (Private)  | All changes including private configs |
| `master-upstream` | `upstream` (Public) | Public-safe changes only              |

### Setup

```bash
# 1. Init from Public repo
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply <github-user>
cd "$(chezmoi source-path)"

# 2. Add Private repo as origin
git remote rename origin upstream
git remote add origin <private-repo-url>

# 3. Configure branch tracking
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
git checkout -b master-upstream upstream/master
git config branch.master-upstream.remote upstream
git config branch.master-upstream.merge refs/heads/master
git config branch.master-upstream.pushremote upstream

# 4. Initial push to Private
git push -u origin master
```

### Workflow

```bash
# Work on master — pushes to Private
git push                                    # → origin (Private)

# Sync public-safe changes to Public
git checkout master-upstream
git merge master                            # or cherry-pick
git push                                    # → upstream (Public)

# Pull Public updates into Private
git checkout master-upstream && git pull
git checkout master && git merge master-upstream
```

## Platform Support

- Linux (Ubuntu/Debian)
- macOS
