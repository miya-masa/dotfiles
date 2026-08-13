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
- `dot_codex/` → `.codex/` (Codex controller instructions, workflow skills, and native agents)
- `dot_agents/` → `.agents/` (skills shared by Claude Code / Codex / opencode, plus the shared workflow core under `workflows/software_delivery/`)

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
- `32` - npm packages (including Codex CLI)
- `33` - Claude skills
- `35` - Codex configuration and shared-skill visibility
- `99` - Set zsh as default shell

### Core Components

**Shell**: Zsh with Zinit plugin manager, platform-specific configs (`dot_zshrc_darwin`, `dot_zshrc_linux`). Custom fzf-powered functions: `fbr` (git branch switch), `cd-git` (ghq repo jump), `sshf` (SSH host picker), `tm` (tmux session picker).

**Editor**: Neovim with LazyVim framework (`dot_config/nvim/lua/plugins/` for custom plugins). LazyVim extras are configured in `dot_config/nvim/lazyvim.json`.

**Terminal**: Tmux with TPM, WezTerm/Ghostty/Alacritty with Catppuccin theme

**herdr**: A tmux-compatible terminal multiplexer added as a first-class alternative in stage 1 of a tmux → herdr migration (prefix `Ctrl+s`, same as tmux). Config is chezmoi-managed under `dot_config/herdr/` (`~/.config/herdr/config.toml`, `~/.config/herdr/layouts/`); `hp` (`dot_zsh/herdr.zsh`) is the fzf-driven session launcher (herdr's counterpart to `tp`). Tmux (TPM, tmuxp, `tp`/`tm`, cc-pane) remains in place for now — removal is a separate stage-2 change. Manage only the individual files (`config.toml`, `layouts/*.json`): a running server keeps its socket, `session.json`, and logs in the same directory, so `~/.config/herdr/` must never become an `exact_` target. Agent integrations (`herdr integration install claude|codex`) are installed idempotently by `.chezmoiscripts/run_onchange_after_17-install-herdr-integrations.sh`; the hook files themselves are owned by the herdr installer and are deliberately not chezmoi-managed. `dot_config/worktrunk/config.toml` has a `[[post-start]]` hook that opens worktrunk worktrees as herdr workspaces when `HERDR_ENV=1`. The `codex-doublecheck` and `ci-monitor` skills, plus `product-discovery`'s spec review gate and `execute-plan`'s final review (Codex cross-model concurrency), branch to a herdr path under `HERDR_ENV=1` and keep their original path otherwise. herdr mechanics for all of these are centralized in the shared `herdr-delegate` skill (`dot_agents/skills/herdr-delegate/SKILL.md`; three modes — `agent`, `command:one-shot`, `command:resident`), which is deliberately disabled for Codex itself (`.chezmoiscripts/run_onchange_after_35-configure-codex.sh.tmpl`) so a delegated Codex agent cannot spawn further agents. Cross-model concurrency defaults on and is toggled off via `~/.claude/data/harness/cross-model-off` (command mode is unaffected). See README.md for the full tmux → herdr key mapping, the stage-1 behavior gaps, and the measured CLI pitfalls (`wait-output` matching the command echo, `pane read` returning plain text, `agent prompt --wait` returning `done` while blocked on an approval screen).

**Languages**: mise manages versions (Go, Node, Python, Lua, Zig, etc. - see `dot_mise.toml`)

**Claude Code**: Custom skills (`dot_claude/skills/`) and agents (`dot_claude/agents/`) are chezmoi-managed. The software delivery workflow is self-hosted as six phase skills (`product-discovery`, `implementation-planning`, `execute-plan`, `ship-change`, `execute-and-ship`, `post-merge-cleanup`) plus the read-only `task-reviewer` subagent, with `start` / `bugfix` / `investigation` / `handoff` around them; the Superpowers plugin is disabled and the workflow has no plugin dependency.

**Codex**: A Terra Medium controller, six phase skills (`product-discovery`, `implementation-planning`, `execute-plan`, `ship-change`, `post-merge-cleanup`, and `execute-and-ship`) plus retained `systematic-debugging`, and bounded Luna/Sol native agents are managed under `dot_codex/`. Shared skills remain in `dot_agents/skills/`, while the installer disables broad workflow and Claude-specific skills that Codex should not auto-load. The state/artifact/snapshot/cleanup helpers and the review references are shared with Claude Code under `dot_agents/workflows/software_delivery/`; Codex keeps its own adapter references in `dot_codex/workflows/software_delivery/references/`.

### Key Bindings

- **Tmux prefix**: `Ctrl+s` (not default `Ctrl+b`)
- **Tmux split**: `|` (vertical), `-` (horizontal)
- **Neovim leader**: `,`
- **Zsh**: `Ctrl+e Ctrl+e` (git branch), `Ctrl+g` (ghq cd), `Ctrl+r` (history)

### Platform Differences

Templates (`.tmpl` files) use Go templating with `{{ if eq .chezmoi.os "linux" }}` for platform-specific logic. Separate Brewfiles exist for macOS (`Brewfile_mac`) and Linux (`Brewfile_linux`).

### Git Branch Strategy

This repo uses a public/private split. `master` branch pushes to `origin` (private), `master-upstream` pushes to `upstream` (public). When making changes, consider whether they contain private information before syncing to upstream.
