# 1Password CLI get-started (公式 docs サマリ)

出典: https://developer.1password.com/docs/cli/get-started/ / https://developer.1password.com/docs/service-accounts/

## Claude セッションでの推奨: service account 方式

Claude セッションの Bash tool は GUI プロンプトを受けられないため、desktop app integration の `op signin` (生体認証) は使えない。**service account token** をセットして使う。

- 環境変数 `OP_SERVICE_ACCOUNT_TOKEN` をセットすれば `op read` / `op run` / `op inject` / `op item` が自動的に service account 認証で動く (`ops_` で始まる token)。
- token は `~/.config/op/service-account-token` (`chmod 600`) に置き、**各 op コマンドの直前で注入**する:
  ```bash
  OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token)" op read op://vault/item/field
  ```
- 確認: `op whoami` (User Type: SERVICE_ACCOUNT を返す)。公式の確認コマンドは `op user get --me`。
- 注意: `OP_CONNECT_HOST` / `OP_CONNECT_TOKEN` がセットされていると `OP_SERVICE_ACCOUNT_TOKEN` より優先される。

### service account の作成 (ユーザー作業)

```bash
op service-account create <serviceAccountName> --expires-in <24h|30d|90d> \
  --vault <vault-name>:read_items[,write_items][,share_items]
```

- 権限: `read_items` / `write_items` (read_items 必須) / `share_items` (read_items 必須)。複数 vault は `--vault` を繰り返す。`--can-create-vaults` 任意。
- **token は作成時1回だけ表示される** (再表示不可)。直ちに token ファイルへ書き、1Password 本体にも保存しておく。
- マルチ vault の service account では `op item get/list` に `--vault <name>` が必須。

## 対応環境

- OS: macOS / Windows / Linux
- Shell: macOS/Linux は bash, zsh, sh, fish。Windows は PowerShell
- macOS は Big Sur 11.0.0 以降
- Linux で desktop app integration を使う場合は PolKit + auth agent が必要
- 1Password サブスクリプションと desktop app (integration 利用時) が前提

## インストール

OS ごとの公式手順に従う。本リポジトリでは chezmoi script `13-install-1password.sh.tmpl` が Ubuntu 向けに自動セットアップ済 (macOS は Brewfile)。

## (参考) Desktop app integration — GUI 環境向け

> 以下は人間が手元の GUI 環境で使う場合の参考。**Claude セッションでは生体認証プロンプトがブロックするため使わない** (上記 service account 方式を使う)。

1Password アプリ側で integration を有効化すると、CLI がアプリの sign-in 状態を共有できる。

- **macOS**: アプリを開いてロック解除 → Settings > Developer > 「Integrate with 1Password CLI」をオン。Touch ID 利用も可
- **Windows**: Windows Hello を有効化 → Settings > Developer > 「Integrate」をオン
- **Linux**: Settings > Security > 「Unlock using system authentication」をオン → Settings > Developer > 「Integrate」をオン

Integration を有効化した状態で何らかの `op` コマンド (例: `op vault list`) を実行すると初回 sign-in プロンプトが出る。

## (参考) サインインの選択肢 — GUI 環境向け

- **App integration**: `op signin` (デスクトップアプリの認証を共有)
- **複数アカウント**: `op signin --account <shorthand>` または `OP_ACCOUNT=<shorthand> op ...`
- **Integration が使えない環境 (CI / リモートサーバー)**: service account 方式 (上記) を使うか、`op account add` で sign-in address・email・secret key を登録した上で `op signin`
