---
name: herdr-delegate
description: "herdr ペイン内で別の agent やコマンドを並走させるための共有契約。呼び出し元 skill（product-discovery / execute-plan / codex-doublecheck / ci-monitor 等）から `herdr-delegate` の agent / command:one-shot / command:resident いずれかのモードとして明示的に参照されたときだけ使う。ユーザーの自然文（「並列で走らせて」「別ペインで動かして」等）だけでは発火しない。HERDR_ENV=1 が前提。"
---

# herdr-delegate

herdr の別ペインで agent（クロスモデル委譲）またはコマンドを走らせるための契約。各呼び出し元 skill は herdr 手順と落とし穴回避をここに委ね、固有の停止条件・監視対象・ユーザー承認だけを自分の SKILL.md に残す。

前提: `test "${HERDR_ENV:-}" = 1`。不成立ならこの契約は成立せず、呼び出し元は自身の非 herdr 経路へ進む。

ヘルパー `herdr-delegate`（`dot_local/bin/executable_herdr-delegate`、PATH 上）が prompt 組み立て・JSON パース・完了判定・孤児選別・隔離引数生成・隔離検証の 6 サブコマンドを提供する: `build-prompt` / `parse-pane` / `check-marker` / `select-orphans` / `build-launch-args` / `verify-profile`。散文では quoting 事故と隔離漏れを防げないため、これらは必ずヘルパー経由で行い、手で組み立てない。

## 識別子と委譲記録

- **agent 名**: `hd-<workflow-id 末尾8hex>-<role>-<gen>`（32 文字制約 `[a-z][a-z0-9_-]{0,31}` を満たす。例 `hd-780ecd3f-review-2` = 20 文字）。世代 `gen` は同一 workflow の再実行で名前が衝突するのを避けるための連番。
- **委譲記録**: `.aidocs/workflows/<id>/delegations.json`。世代の採番元。
  ```json
  {
    "version": 1,
    "next_generation": 3,
    "delegations": [
      {"generation": 1, "role": "review", "agent_name": "hd-780ecd3f-review-1",
       "pane_id": "wD:p7", "mode": "agent", "state": "held"},
      {"generation": 2, "role": "review", "agent_name": "hd-780ecd3f-review-2",
       "pane_id": "wD:p9", "mode": "agent", "state": "closed"}
    ]
  }
  ```
  - `state`: `active`（走行中）/ `held`（`blocked` 残置または resident。回収対象外）/ `closed`（片付け済み）。
  - `mode`: `agent` / `command:one-shot` / `command:resident`。
- **所有権の一次キーは agent 名**。`agent get <pane_id>` は成功するが kind 名（`codex` 等）を渡すと `agent_not_found` になる実測があるので、**ターゲットは常に pane ID**を使う。`command` モードは agent を持たないので pane ID と役割を artifact に記録して識別し、`pane rename` の `label` は補助表示として使ってよい（`pane get` / `pane list` の JSON に出ることを実測済みだが、server 再起動後の永続性は未検証なので権威にしない）。

off スイッチの判定は呼び出し元 skill の責務であり、この契約は関知しない（Claude 固有 path をここに持ち込まない）。

## 3 モード

| モード | 用途 | ライフサイクル |
|---|---|---|
| `agent` | 別モデルへの委譲（クロスモデルレビュー） | 1 回で完結。回収後に close |
| `command:one-shot` | 完了シグナルのあるコマンド（CI 監視） | `wait-output` 後に close |
| `command:resident` | 常駐（`--loop` 等） | ターンをまたいで生存。停止と close はユーザー承認後のみ、契約側から勝手に close しない |

## 全モード共通のルール

- ペイン確保は `herdr pane split --current --direction <geometry> --cwd <呼び出し元が渡した絶対パス> --no-focus`。`$PWD` を既定にしない。ID は `.result.pane.pane_id` から取る（`parse-pane` サブコマンドでパースする）。
- geometry は `herdr pane layout` で決める。過密で最小幅を割るなら分割せず fail-soft する（狭いペインは screen 検出を劣化させ `unknown` を誘発する）。
- **`--no-focus` を守り、`agent focus` / `pane focus` を使わない。** `focus` 系コマンドは `done` を seen 扱いにしてしまい、workspace をまたぐ move で pane ID が変わる。
- **非 idle 中の画面取得は `pane read <pane_id> --source visible`。** `agent read` は非 idle 中 `agent_not_idle` を返すが `pane read` は状態非依存に読める。
- 一時ファイルの生成は Write tool か `<<'EOF'`（クォート済みデリミタ）でのみ行う。変数展開のあるリダイレクト（`echo "…" >`、クォート無しヒアドキュメント）は書き込み時点で展開・実行されるため使わない。
- 片付けは自分が起動した agent 名 / 記録した pane ID だけを対象にする。ID 失効時（ユーザーが手で閉じた・別 workspace へ移した）の close 失敗は無視し、fail-soft 経路を巻き添えにしない。`pane close` に `--force` 相当は無いため、失敗時はユーザーへ pane ID を提示して終える。
- **孤児回収**: 起動時に `herdr agent list` と `delegations.json` を `select-orphans --agent-list-json - --records <path> --current-generation N` に通す。`state == "held"`（`blocked` 残置・resident）、`mode != "agent"`、`generation >= 現世代` を除外し、**前世代の active な agent モードだけ**を回収対象にする。ユーザーや他 skill のペインには触れない。出力される agent 名を `delegations.json` で pane_id に引き直してから close する（close の対象は常に pane ID）。

## 隔離方針（`agent` モード専用）

`agent` モードの委譲先は、リポジトリではなくレビュー用 scratch ディレクトリ（`mktemp -d`）を cwd として起動する。

```
<scratch>/
├── input/      ← spec / diff / plan をコピーして置く
└── out/<name>.md  ← 回収先
```

- 隔離は **permission profile による default-deny** で作る。**`--sandbox` フラグは渡さない**（渡すと profile 自体が無効化され、`workspace-write` に落ちて read が全 FS へ素通りする）。読み取り許可は `":minimal"` とツールチェイン root（`command -v codex` の解決先を `build-launch-args` が導出する）の 2 つに限り、`<scratch>` にだけ write を与える。deny glob（`"**"="deny"` 等）は**使わない**。`bwrap` は最大引数数 9000 を超えると `Exceeded maximum number of arguments` で全コマンドを起動不能にするため、default-deny + 許可列挙で組む。
- 許可 root の値をハードコードしない。`build-launch-args --scratch D --profile-name N [--repo-root R]` が `command -v` の戻りから解決して組み立て、解決結果が repo や `.aidocs/` の祖先になっていないか（および `$HOME` 等の広域 root でないか）を祖先ガードで検査する。ガードに違反したら非ゼロ終了する。
- **`agent start` の前に必ず `verify-profile --scratch D --profile-name N --repo-root R` を通し、0 を返した時だけ続行する（非ゼロなら agent を起動せず fail-soft）。** これは同一 profile・同一起動形の canary を `codex sandbox` でゼロクォータに 2 本打つ: **正**（`test -e <scratch>` → 見えるはずなので 0 を期待）と**負**（`test -e <repo 直下に実在するエントリ（名前昇順の先頭）>` → 不可視のはずなので非ゼロを期待。特定のファイル名に依存させないのは、その名前が無い repo で「不在」を「不可視」と誤読して fail-open するのを避けるため）。**両方が期待どおりの時だけ 0** を返し、判定は終了コードのみで行う（メッセージ文字列を見ない）。正を併せて打つのは、負だけでは「隔離成立」と「canary がそもそも起動できていない」を区別できないため — `--permission-profile` を持たない codex（v0.129 未満）はパースエラーで非ゼロ終了するので、負だけの判定では**隔離ゼロのまま fail-open** する。この 2 本立てが version gate と `bwrap` 起動失敗の検出を兼ねる。
- **隔離が及ぶのはモデルが起動する子プロセスだけ**で、codex プロセス自身の会話ログ（`~/.codex/history.jsonl`、session rollout、sqlite）は sandbox 外に書かれる。scratch を削除しても、渡した入力は codex 側に残る。「書き込めるのは scratch のみ」はモデルが実行するコマンドについての主張であり、codex プロセス自体の永続化には及ばない。

## `agent` モードの手順

1. `command -v codex` で事前確認し、絶対 path を解決して保持する（PATH に無いと `agent start` は 30 秒 timeout する）。無ければ即 fail-soft。**この確認は controller の cwd で行うため委譲先の cwd（scratch）での可用性は保証しない**。scratch を cwd にすると mise が別バージョンの node を選び `codex` が PATH から消えることがある。
2. scratch を作り、入力を `<scratch>/input/` へコピーする。
3. `build-launch-args --scratch <scratch> --profile-name <name> --repo-root <repo> --env-out <f>` で、`agent start` の `--` 以降に渡す argv（1 行 1 引数）と、次の手順で使う `--env` の値を得る。`--env-out` が書き出すのは展開済みの完成値なので、`PATH=…` を手で組み立てない。
4. `herdr pane split --cwd <scratch> --env "$(cat <f>)" --no-focus` でペインを確保する。**`--env` は必須**で、省くと手順 1 の false positive のまま `agent start` が 30 秒 timeout する。`pane read --source visible` で shell プロンプト到達を確認する（zsh + Zinit + mise で起動が遅い）。
5. `verify-profile` を実行する。**0 を返した時だけ続行し、非ゼロなら agent を起動せず fail-soft**（隔離が効いていない、codex が古い、または canary 自体が起動できない）。
6. `herdr agent start hd-<8hex>-<role>-<gen> --kind codex --pane <pane_id> -- <build-launch-args の出力>`（`-c "permissions.<name>={…}"` `-c 'default_permissions="<name>"'` `-c approval_policy="never"` `-c model_reasoning_effort="high"`）。`build-launch-args` の各出力行は single quote で包んで渡す（出力に `'` と改行が含まれないことを helper が保証している）。`approval_policy="never"` は default-deny 下で codex が権限昇格を要求して承認画面（＝ `blocked` 終端）に落ちるのを防ぐため。codex に `--effort` フラグは無い。**`--sandbox` は渡さない。**
7. **投入前ゲートは「状態 かつ 画面」の連言。** `agent get` が idle 系であることに加え、`pane read --source visible` で composer プロンプト（入力欄）を**肯定的に**確認できたときだけ投入する。確認できなければ画面内容・pane_id・到達手段を提示して停止する。`--wait` は承認画面で止まっていても `done` を返すことがあり、`blocked` / `unknown` の除外だけでは素通りするため。
8. prompt は `build-prompt --instruction-file F --input-dir <scratch>/input --output-path <scratch>/out/<name>.md` で組み立て、一時ファイルへ書いた上で `herdr agent prompt <pane_id> "$(cat "$f")" --wait` の形でのみ渡す。単一引数の上限は `MAX_ARG_STRLEN`（131072、`getconf ARG_MAX` の値ではない）で、100KiB を超える argv は分割せず fail-soft とする。
9. **完了判定の一次は `check-marker --path <scratch>/out/<name>.md` が 0 を返すこと**（ファイルが存在し、末尾に `<!-- DELEGATE-COMPLETE -->` を持つ）。herdr の状態は補助。マーカーが無い間は sleep-poll（例 5s × N）で待ち、上限で fail-soft とする。`agent wait` は `--until` 省略時に既に settled なら即返って busy-spin になるため一次判定には使わない。`--wait` / `agent wait` の戻りを単独の完了根拠にしない（`--wait` は turn を追跡せず、既に working 中なら別 turn の完了で満たされうる）。
10. `agent prompt` が `agent_prompt_stalled` を返した場合、**close / retry の前に `pane read --source visible` で投入痕跡を確認する**。`agent_prompt_stalled` は「投入後 5 秒以内に lifecycle 変化が観測できなかった」であり、本文は投入済みであることが多い。投入済みなら close / retry せず待機を続ける（二重投入とクォータ浪費を防ぐ）。
11. 回収した md の原本を `reviews/` に保存し、**kind / model / effort（`codex` / `gpt-5.6-sol` 等 / `high`）を evidence に残す**。scratch は回収後に削除する。

## `command` モードの手順

- **one-shot**: `pane run` → `pane wait-output`（`--match` のトークンを投入コマンド文字列に出さない。`pane wait-output` は投入コマンド行のエコーにもマッチするため、出力側にしか現れない語を使うかリテラルを分割する）→ `pane read` → close。
- **resident**: `pane run` で常駐起動しペインを残したままターンを終える。停止は呼び出し元 skill の契約（ユーザー承認 → `send-keys ctrl+c` → close）に従い、この契約側から勝手に close しない。
- `command` モードの cwd は呼び出し元の作業ディレクトリ（worktree 等）でよい。scratch 隔離は `agent` モード固有。

## 終端状態

| 状態 | 扱い | ペイン |
|---|---|---|
| 正常完了 | 結果を返す | close |
| `blocked` | 第 3 の終端状態。`send-keys` で自動応答せず、画面内容・pane_id・到達手段（herdr サイドバーの attention queue / `prefix+o`）を提示して停止 | **残す**（`delegations.json` に `held` として記録） |
| `unknown` / その他の失敗 | fail-soft（warning を返しユーザーを止めない） | close |

`unknown` は「分類できない」だけで承認 UI の証拠ではなく、狭いペインでも出るためユーザーを止める側に倒さない。

## 落とし穴と回避（実測・公式ドキュメント由来）

| # | 事実 | 契約側の回避 |
|---|---|---|
| P1 | `--wait` は承認画面で止まっていても `done` を返すことがある | 投入前ゲートを「状態 かつ 画面」の連言にする（手順 7） |
| P2 | `--wait` は turn を追跡しない | 完了判定の一次は終端マーカー付きファイル（手順 9） |
| P3 | `agent start` は trust / 承認画面が出ていても返る。対話 TUI 経由でも `--sandbox` を渡さない起動形なら trust 画面は出ない（実測） | canary（`verify-profile`）で隔離を先に確認し、投入前は `pane read --source visible` で composer を肯定的に確認 |
| P4 | `agent prompt <TARGET> <TEXT>` は argv 直渡しのみ。単一引数の上限は `MAX_ARG_STRLEN = 131072` | 本文はファイル経由で渡し、100KiB 超は分割せず fail-soft（手順 8） |
| P5 | `agent read` は非 idle 中 `agent_not_idle` を返す。`pane read` は状態非依存 | 非 idle の画面取得は常に `pane read --source visible` |
| P6 | alternate screen から出た行は host scrollback に入らず、`--lines` を増やしても `recent-unwrapped` で回収できない | 初回 prompt からファイル出力を指示する（後述「prompt 作法」で herdr 公式 skill:185 を上書き） |
| P7 | `agent start` は対象 CLI が PATH に無いと 30 秒 timeout | `command -v codex` の事前確認（手順 1） |
| P8 | `pane wait-output` は投入コマンド行のエコーにもマッチする | `--match` / `--regex` のトークンをコマンド文字列に出さない（command モード） |
| P9 | `agent_prompt_stalled` は atomically submit した後の lifecycle 待ちで返る＝本文は投入済み | close / retry の前に投入痕跡を確認（手順 10） |
| P10 | 入れ子 herdr は `nested herdr is disabled` | 前提の `HERDR_ENV=1` 確認のみで herdr 自身を委譲先の子として起動しない |
| P11 | `agent wait` は `--until` 省略時、既に settled なら即返る（busy または非 busy を問わずリトライループが busy-spin になる） | 一次判定に `agent wait` を使わず sleep-poll + 終端マーカーで待つ |
| P12 | `agent focus` / `pane focus` は `done` を seen 扱いにする。workspace をまたぐ move で pane ID が変わる | `--no-focus` を守り focus 系を使わない |
| P13 | `pane rename` のラベルは `pane list` / `pane get` の JSON に出る（server 再起動後の永続性は未検証） | 権威は `delegations.json`。label は補助表示に留める |
| P14 | agent 名の制約は `[a-z][a-z0-9_-]{0,31}`（32 文字上限） | `hd-<8hex>-<role>-<gen>` 形式で規定 |
| P15 | scratch（`/tmp` 配下）を cwd にすると mise が別の node を選び、`codex` が PATH から消える | `pane split --env` に `build-launch-args --env-out` の値を渡す（手順 3〜4） |
| P16 | `--sandbox` フラグを渡すと permission profile が無効化される | `agent start` に `--sandbox` を渡さない（手順 6） |
| P17 | permission profile の deny glob（`"**"="deny"`）は `bwrap: Exceeded maximum number of arguments 9000` で全コマンドを起動不能にする | default-deny + 読み取り許可の列挙で組む（`build-launch-args`） |

## prompt 作法

- 委譲先が GPT 系なら `writing-gpt-prompts`、Claude 系なら `writing-claude-prompts` に従う。
- **初回 prompt からファイル出力を指示する。** herdr 公式 skill（`dot_agents/skills/herdr/SKILL.md:185`）は "do not request file output in the initial prompt" としているが、本契約はこれを意図的に上書きする。根拠は 2 点: (a) alternate screen から出た行は host scrollback に入らず `--lines` を増やしても回収できない（P6）ため、初回から回避しないと出力を丸ごと失いうる、(b) 完了判定を状態非依存の終端マーカー付きファイルに載せるため（herdr の状態は補助）。呼び出し元 skill はこの上書きを再掲しない。

## timeout の 2 段構え

Task tool はターンをブロックするため、Opus のレンズ並列が返るまで controller は Codex の状態を見に行けない。**Codex 側 `--wait` の timeout は Opus 側の想定より短く取り**、Task 復帰直後に `agent get` / `check-marker` で取り直す。これにより、ブロックされている間に Codex 側が完了・停止していても、復帰後の 1 手で検知できる。
