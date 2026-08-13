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
- **herdr**: tmux 代替の terminal multiplexer。第 1 段階の移行として追加済み（tmux は段階移行のため引き続き残置）。詳細は下記「herdr（tmux からの段階移行）」参照
- **Languages**: mise (Go, Node, Python, etc.)
- **Tools**: fzf, ripgrep, lazygit, lazydocker, ghq, delta
- **AI agents**: Claude Code's global instructions live in `dot_claude/CLAUDE.md`; Claude Code and opencode share skills from `.agents/`; Claude Code and Codex run the same six-phase software delivery workflow (`product-discovery`, `implementation-planning`, `execute-plan`, `ship-change`, `post-merge-cleanup`, and `execute-and-ship`) on top of a shared workflow core in `.agents/workflows/software_delivery/` (state/artifact/snapshot helpers and review lenses); Codex additionally keeps `systematic-debugging`, native subagents, and selected shared skills

### herdr（tmux からの段階移行）

tmux に代わる terminal multiplexer として herdr を第 1 段階で追加した。tmux 一式（`dot_tmux.conf` / TPM / tmuxp / `tp` / `tm` / cc-pane）は段階移行のため引き続き残置しており、撤去は第 2 段の別対応とする。

- **起動 / 再 attach**: `herdr` で起動・再 attach する。**tmux の外側で起動すること**（tmux の内側で起動するとキーが tmux の prefix に奪われる）
- **detach**: `prefix+d`
- **prefix**: `Ctrl+s`（tmux と同じ）
- **設定**: `~/.config/herdr/config.toml` と `~/.config/herdr/layouts/`（chezmoi source は `dot_config/herdr/`）
- **`hp`**: fzf でディレクトリと layout（`dev` / `mac` / `tile`）を選んで herdr セッションを起動するランチャー（`tp` の herdr 版）。herdr サーバ起動中に使う
- **skill 再生成**: herdr を上げたら `herdr --skill > dot_agents/skills/herdr/SKILL.md` を実行して差分を取る（出力は加工しない）
- **サイドバーの attention queue**: `agent_panel_sort = "priority"` を設定しているため、サイドバーの agent 一覧が space 順ではなく「今見るべき順」に並ぶ。herdr は各ペインの agent を `working` / `blocked`（承認・質問待ち）/ `done`（未確認のまま完了）/ `idle`（確認済み）に分類する。`prefix+o` で通知の発生元ペインへジャンプできる
- **agent integration**: `.chezmoiscripts/run_onchange_after_17-install-herdr-integrations.sh` が `herdr integration install claude` / `codex` を冪等に流す。integration は agent の session id を herdr に渡してセッション identity / restore を補助する（ペインの `working` / `blocked` / `done` / `idle` は screen manifest で判定され、integration が transcript を読み続けるわけではない）。hook 本体（`~/.claude/hooks/herdr-agent-state.sh`、`~/.codex/herdr-agent-state.sh`、`~/.codex/hooks.json`）は herdr installer が所有し再インストールで上書きされるため chezmoi では管理しない。hook は `HERDR_ENV` / `HERDR_SOCKET_PATH` / `HERDR_PANE_ID` が揃わないと即 exit するので tmux 側の cc-pane とは干渉しない
  - 反映は **新しい agent セッションから**。通常は SessionStart、Codex fallback は最初の UserPromptSubmit で紐付ける。紐付いたかは `herdr agent get <pane>` の `agent_session` で確認する（`herdr-server.log` にはこの報告が一切残らないので、ログは判定に使えない）
  - **codex は integration 導入後の初回起動で "Hooks need review" の承認画面を出す。** trust しないと hook は走らない（`~/.codex/config.toml` の `[hooks.state."~/.codex/hooks.json:session_start:0:0"]` が `enabled = true` かで確認できる）
  - **Codex 0.147 の SessionStart に transcript_path が無い場合の fallback**: `~/.local/bin/herdr-codex-session-bridge` を UserPromptSubmit に登録し、rollout が materialize した後の非空 `transcript_path` を SessionStart 形に変換して Herdr の生成 hook へ渡す。これで session identity と Herdr server 再起動後の native resume を補助できるが、ライフサイクル状態の判定は引き続き screen manifest のまま（identity が欠けると native resume に影響する）。integration 導入後の初回起動では Codex の "Hooks need review" を **trust** し、hook 設定を読み込ませるため **新しい Codex セッション**を起動する。trust しない場合や bridge がまだ実行されない場合も `agent start` / `agent prompt` / `agent read`（= `codex-doublecheck` の herdr 経路）による画面ベースの検出は動く
  - herdr を上げたら `herdr integration status --outdated-only` を確認し、古ければ入れ直す（codex 側は上記が直っているか併せて確認する）
- **worktrunk 連携**: `dot_config/worktrunk/config.toml` の `[[post-start]]` に、herdr の中で作った worktree を workspace として開く hook がある（`HERDR_ENV` が無ければ no-op）。`herdr worktree open` は**親リポジトリ workspace から始める必要がある**ため `--cwd` には `--git-common-dir` から導出した親 root を渡す（worktree のパスを渡すと `linked_worktree_source` で失敗する）。既に開いていれば `already_open` が返るだけで workspace は増えない。ただし**初回は親リポジトリの workspace も併せて作られる**ので、worktree 1 個につき workspace が 2 個生えることがある
- **skill 側の herdr 経路**: `codex-doublecheck`（隣のペインで codex を起動して結果まで回収）、`ci-monitor`（CI ポーリングをペインに逃がす）、`product-discovery` / `execute-plan`（spec review gate と final review での Codex クロスモデル並走）が `HERDR_ENV=1` のときだけ herdr 経路に分岐する。herdr の外では従来経路のまま
- **共有契約 `herdr-delegate`**: 上記 skill の herdr 手順（ペイン確保・投入・完了判定・隔離・片付け）は `dot_agents/skills/herdr-delegate/SKILL.md` に一本化されており、`agent`（クロスモデル委譲）/ `command:one-shot`（CI 監視等）/ `command:resident`（常駐プロセス）の 3 モードを持つ。各呼び出し元 skill は固有の停止条件・監視対象だけを自分の SKILL.md に残す。並走の off スイッチは `~/.claude/data/harness/cross-model-off`（`command` モードの ci-monitor は対象外）。委譲先の Codex が更に agent を起動しないよう、`herdr-delegate` 自体は Codex の skill 一覧から無効化されている（`.chezmoiscripts/run_onchange_after_35-configure-codex.sh.tmpl`）

#### 主要キー対応（tmux → herdr）

| tmux | herdr |
| --- | --- |
| prefix `C-s` | `Ctrl+s`（同じ） |
| `bind \|` 右分割 | `prefix+\|` |
| `bind -` 下分割 | `prefix+-` |
| `bind C-p` / `C-n` | `prefix+Ctrl+p` / `prefix+Ctrl+n`（前/次タブ） |
| `bind r` 設定再読込 | `prefix+r` |
| `bind e` 同期入力 | `prefix+e`（popup に入力 → **同じ tab の**ペインへ 1 回送信。agent が検出されているペインは除外（`idle` でも除外）） |
| detach | `prefix+d` |
| rename / close tab | `prefix+,` / `prefix+&` |
| choose-session | `prefix+s`（workspace picker） |
| `bind -r H/J/K/L` リサイズ | `prefix+Shift+r`（リサイズモード） |
| copy-mode | `prefix+[` |
| zoom / close pane / new tab / タブ番号 | `prefix+z` / `prefix+x` / `prefix+c` / `prefix+1..9`（herdr 既定と同じ） |
| vim-tmux-navigator `C-h/j/k/l` | `Ctrl+h/j/k/l`（nvim / fzf の中は pass-through、それ以外はペイン移動） |

herdr 既定のうち退避したもの: settings = `prefix+Shift+s`、scrollback 編集 = `prefix+Shift+e`。既定のままのもの: goto = `prefix+g`、サイドバー開閉 = `prefix+b`、ペイン移動 = `prefix+h/j/k/l`。

#### CLI の落とし穴（実測・herdr 0.8.0）

- **`pane wait-output` は打ち込んだコマンド行のエコーにもマッチする。** `herdr pane run PANE 'cmd; echo DONE'` の直後に `--match DONE` を待つと、出力ではなくコマンド行に即マッチして 0.001 秒で返る。待ち受けトークンが投入コマンド文字列に現れない形にする（`printf "DONE""_TOKEN\n"` のようにリテラルを分割する / `--regex` を出力側にしか現れない形にする）
- **`pane read` / `agent read` はプレーンテキストを返す。** 多くのコマンドが JSON を返すのに対しこの 2 つは例外で、`jq` に通すと黙って空になる
- **`--source recent-unwrapped` は出力がスクロールするまで空を返す。** 短い出力の段階では `--source visible`（ビューポート分のみ）を使う
- **`agent prompt --wait` が `done` を返しても完了とは限らない。** 承認画面で止まっていても herdr が `blocked` と分類できず `done` を返すことがある（codex の "Hooks need review" で実測）。`agent read` で画面を確認するまで結果を受け取ったと判断しない
- **`agent start` は対象の CLI が PATH に無いと 30 秒 timeout する。** mise 管理のツールはディレクトリによって PATH に載らない。timeout したら `pane read` で `command not found` を確認する
- **隔離 probe を立てるときは `HERDR_*` も落とす。** herdr ペインの中から probe を起動すると `nested herdr is disabled` で失敗する:

  ```sh
  tmux -L hprobe -f /dev/null new-session -d -x 200 -y 50 \
    'env -u TMUX -u TMUX_PANE -u HERDR_ENV -u HERDR_PANE_ID -u HERDR_SOCKET_PATH \
         -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID herdr --session probe; exec cat'
  # 以後 HERDR_SOCKET_PATH=~/.config/herdr/sessions/probe/herdr.sock を明示
  # 片付け: herdr session stop probe / herdr session delete probe / tmux -L hprobe kill-server
  ```

#### 第 1 段で失われる挙動

- `synchronize-panes` の**持続モード**は無い（`prefix+e` は 1 回送信のみ）
- `prefix+space` の**レイアウト巡回**は無い（herdr の `layout.apply` が対象 tab のプロセスを全部作り直すため。第 2 段で `pane move` 方式を検討）
- thumbs（`prefix+f` の画面上文字列コピー）は無い
- status への cpu / battery / 時刻の表示は無い（サイドバーは branch と git status のみ）
- copy-mode の `V`（行選択）/ `C-v`（矩形選択）は無い
- `<C-\>` の pane またぎは無い（herdr 内では nvim ウィンドウ内の直前移動に縮退）
- cc-pane の状態表示は herdr 内では更新されない（cc-pane は `TMUX_PANE` 前提のため。Claude 側はガードして無音で何もしない、Codex 側は第 1 段では未対応で notify が失敗する）。代わりに herdr のサイドバーが agent 状態（`working` / `blocked` / `done` / `idle`）を持つ
- `Ctrl+h` 等のペイン移動キーの直後に極めて高速な入力やペーストをすると 1 文字失われうる（shell バインドが非同期のため。人間の打鍵速度では踏まない）
- `prefix+e` の popup は **Esc 単独では閉じない**（Esc 文字が入力欄に混入する。閉じるには `Ctrl+d` か空のまま Enter）

### opencode

Global instructions, agents, and MCP servers are chezmoi-managed under `dot_config/opencode/`.

- `agents/` → symlink to `~/.claude/agents/*.md`（Claude agents 3 個を流用; `tools` 無しの agents のみ。残り 9 個は opencode が tools array を解釈できないため対象外）
- skills は配置不要（opencode が `~/.agents/skills/` を自動 walk）
- superpowers は `.chezmoiscripts/run_onchange_after_34-install-opencode-superpowers.sh` が `obra/superpowers` を `~/.config/opencode/superpowers/` に clone し、plugin と skills を symlink で expose
- `oh-my-openagent` plugin（旧名 `oh-my-opencode`）は `.chezmoiscripts/run_onchange_after_36-install-opencode-plugins.sh` が bun/npm install

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
