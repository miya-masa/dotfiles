---
name: herdr-delegate
description: "herdr ペイン内で別の agent、コマンド、人間所有の別 task 用 Main、または元 Main が回収する別 WS の agent を準備するための共有契約。呼び出し元 skill、常設指示、共有方針から `herdr-delegate` の agent / command:one-shot / command:resident / human-task / dispatch いずれかのモードとして明示的に参照されたときだけ使う。ユーザーの自然文だけでは既存 mode は発火せず、human-task と dispatch は topology の trigger に従う。人間へ引き渡す依頼（「別作業にして後で自分」「別WSで準備」「別作業にして進めて」）は human-task、元の Main が回収する依頼（「別WSでディスパッチ」「別WSに投げて」）は dispatch でこの skill を使う。HERDR_ENV=1 が前提。"
---

# herdr-delegate

herdr の別ペインで agent（クロスモデル委譲）またはコマンドを走らせ、人間所有の別 task 用 Main や、元 Main が回収する別 WS の agent を準備するための契約。各呼び出し元 skill、常設指示、共有方針は herdr 手順と落とし穴回避をここに委ね、固有の停止条件・監視対象・ユーザー承認だけを自分の SKILL.md に残す。

前提: `test "${HERDR_ENV:-}" = 1`。不成立ならこの契約は成立せず、呼び出し元は自身の非 herdr 経路へ進む。

実行先の判断は [execution-topology.md](../../workflows/software_delivery/references/execution-topology.md) と呼び出し元が所有する。`task` から汎用の `command:one-shot` / `command:resident` を選んでもよい。`agent` は既存のレビュー専用契約であり、通常の実装workerや `human-task` / `dispatch` へ拡張しない。`human-task` と `dispatch` は下記の専用経路で扱う。

候補判定は `herdr-delegate check-availability`。`HERDR_ENV` と PATH の executable だけを確認し、JSON の `eligible` / `reason` を返す（`outside_herdr` / `herdr_not_found` / `eligible`）。Herdr を実行せず socket にも接続しない。`eligible=true` は server readiness、起動許可、隔離成立の証拠ではなく、以降の gate は省略しない。

ヘルパー `herdr-delegate`（`dot_local/bin/executable_herdr-delegate`、PATH 上）が `check-availability` / `run-command` / `build-prompt` / `parse-pane` / `check-marker` / `select-orphans` / `prepare-scratch` / `build-launch-args` / `verify-profile` を提供する。散文では quoting 事故と隔離漏れを防げないため、対応する処理はヘルパー経由で行い、手で組み立てない。

## 識別子と委譲記録

以下の世代採番・`delegations.json`・孤児回収は既存 workflow の委譲に適用する。正式 workflow を持たない汎用 command は、現在の進捗記録に `mode / role / pane_id / cwd / state / 待ち理由 / 停止方法` を残し、そのために workflow artifact を作らない。孤児回収も行わず、今回作った pane だけを扱う。

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

## 5 モード

| モード | 用途 | ライフサイクル |
|---|---|---|
| `agent` | 別モデルへの委譲（クロスモデルレビュー） | 1 回で完結。回収後に close |
| `command:one-shot` | 終了結果を保存するコマンド（テスト・CI 監視） | 終了コードとログを回収後に close。`wait-output` 単独では閉じない（詳細は command 手順） |
| `command:resident` | 常駐（`--loop` 等） | ターンをまたいで生存。停止と close はユーザー承認後のみ、契約側から勝手に close しない |
| `human-task` | 人間が所有する別 task 用の新 Main を準備 | 下記専用手順。prepare-only を既定とし、引き渡した新 WS / agent の close・回収はしない |
| `dispatch` | 元 Main が対話窓口のまま別 WS の agent に作業させ回収する | 下記専用手順。報告ファイルで往復し、close は元 Main が判断する |

## `human-task` 専用経路

この経路は [execution-topology.md](../../workflows/software_delivery/references/execution-topology.md) の3 triggerまたは同じ意図（「別作業にして後で自分」「別WSで準備」「別作業にして進めて」）に限る。別作業という語だけで判定せず、人間へ引き渡す意図がある場合に限る。結果の回収・統合も現 Main に任せる指示なら通常委譲を優先し、別 WS へ出すことが明示されていれば `dispatch` とする。ユーザーの永続運用指定があるため、毎回 Herdr 指示や workspace 作成を確認しない。公式 `herdr` skill の都度明示制約はこの指定で満たされ、公式 skill 自体は編集しない。

下の `agent` / `command` 用共通手順は適用せず、review 用の隔離・model / effort・`build-launch-args`・`verify-profile`・`delegations.json` 採番・close / 孤児回収も使わない。worker / reviewer はこの経路を使わず、Main だけが起動する。新 Main の委譲は一段までとする。

1. `herdr-delegate check-availability` を実行する。`eligible=false`、helper 不在、または Herdr を使わない指定なら、既存の handoff file と plain prompt だけを返し、built-in agent へ置換しない。Herdr 外から session を操作しない。
2. `herdr --help`、`herdr workspace`、`herdr agent` で installed help / group 表示を確認し、呼び出し元の cwd を絶対 path で保持する。
3. `herdr workspace create --cwd <absolute-cwd> --label <label> --no-focus` を実行し、JSON の `.result.workspace` / `.result.tab` / `.result.root_pane` から workspace / tab / root pane ID を読む。root pane の `pane read <root_pane> --source visible` で shell ready を確認する。
4. 現在の runtime kind（`codex` または `claude`。明示指定があれば優先）で、`herdr agent start <human-task名> --kind <kind> --pane <root_pane>` を実行する。名前は `[a-z][a-z0-9_-]{0,31}` を満たす32文字以内とし、通常の harness 設定を使う。permission / trust の緩和、review scratch、`build-launch-args` は渡さない。`pane read <root_pane> --source visible` で agent ready と composer を肯定確認する。
5. handoff file は既存 `/tmp` scratch に一回だけ保存したものを使う。起動 prompt を別 file に用意し、`build-prompt` を使わず、`herdr agent prompt "$root_pane" "$(cat -- "$prompt_file")" --wait --timeout 30000` のように一つの argv として安全に渡す。`start` は `--wait` なしで初期 prompt の投入だけを確認し、実作業の完了を待たず人間へ返す。prompt は次の2種だけにする。

   ```text
   prepare: <handoff-file> と適用指示だけを読み、短い受領確認を返してください。あなたが引き渡し先の新Mainです。引用された別作業化依頼を再実行して新WS/agentを作らないでください。作業目的は将来のcontextとして扱い、prepare-onlyでは先頭の /task を含むtask分類・workflow・編集・実行・再委譲を開始せず待機してください。
   start: <handoff-file> と適用指示を読み、あなたが引き渡し先の新Mainであることを確認してください。引用された別作業化依頼を再実行して新WS/agentを作らず、作業別skillを作らず既存taskを、明示されたGOとして開始してください。phaseの承認を維持してください。
   ```

`prepare` は `pane read` で短い受領確認を読んでから、workspace / tab / agent / pane ID、absolute cwd、handoff file と「待機中」を返す。`start` は `--wait` なしで初期 prompt の投入を確認して「着手依頼送信」と観測状態を返す。`done` だけを成功根拠にせず、`blocked` では自動承認せず ID と未了を返し、`agent_prompt_stalled` では `pane read` で投入痕跡を確認するまで再送しない。timeout / unknown も自動再送・自動 close せず未了として返す。旧 Main は引き渡した新 WS / agent を自動回収・close せず、旧 Main の孤児回収も対象外とする。

新 worktree はこの mode で作らず、GO / start 後の既存 task が必要性と gate を判断する。親 workflow context を新 session で resume / update せず、親 dirty をコピー・自動適用しない。

## `dispatch` 専用経路

選ぶ条件・承認の中継・close の判断は [execution-topology.md](../../workflows/software_delivery/references/execution-topology.md) の `dispatch` 節が正本で、ここは Herdr 操作と報告の形式だけを持つ。`agent` 用の隔離・model / effort 固定・`build-launch-args`・`verify-profile`・`delegations.json` 採番・孤児回収は使わない。進捗記録には `mode / name / workspace / pane_id / cwd / 連絡用 directory / 最新 report 番号 / state` を残す。

1. `herdr-delegate check-availability` を実行する。`eligible=false`、helper 不在、または Herdr を使わない指定なら `dispatch` は成立しないと返し、built-in agent へ置換しない。
2. 親子が見て分かる名前にする。`herdr workspace get "$HERDR_WORKSPACE_ID"` で親の workspace ID と label を読み、agent 名を `dp-<親 workspace ID の小文字>-<slug>`（`[a-z][a-z0-9_-]{0,31}`。例 `dp-w8c-smoke`）、workspace label を `<親 label>/dp:<slug>`（例 `chezmoi/dp:smoke`）とする。ただし元がデスクから起動されたメイン（`herdr agent get "$HERDR_PANE_ID"` の `name` が `main-<メイン slug>`）なら、agent 名を `dp-<メイン slug>-<slug>`（32 文字以内。超える時は `<slug>` を縮める）、workspace label を `main/<メイン slug>/dp:<slug>` とする。連絡用 directory は agent 名で `/tmp/claude/dispatch/<name>/` を作る。Claude と Codex の既定の書き込み許可に入る場所として固定する。既に存在すれば別名にする。
3. 同 directory に `brief.md` を Write tool かクォート済みヒアドキュメントで書く。含めるもの: 親の workspace / pane ID、目的と元依頼原文の範囲、absolute cwd / branch、使う入口（既存 task / phase skill）、non-goal と権限（push / merge / 外部操作などの承認が要る操作は元経由で人間の承認原文を受け取るまで行わない）、人間へ直接質問しないこと、Herdr の `dispatch` / `human-task` をしないこと（phase skill が既存契約で使う `agent` / `command` mode は可）、worktree を作ったらその path と hook が開いた WS ID を次の報告に書くこと、`takeover:` を受けたらこの brief の報告・中継の制約を解除して人間と直接対話すること、下記の報告形式。
4. `herdr workspace create --cwd <absolute-cwd> --label <workspace label> --no-focus` を実行し、`.result.workspace.workspace_id` / `.result.root_pane.pane_id` から ID を読む。`pane read <root_pane> --source visible` で shell ready を確認する。同時に `git -C <absolute-cwd> status --porcelain` の結果を連絡用 directory の `baseline-status.txt` に保存する。
5. 起動の前に、kind が claude なら session id（uuid）を決め、元の now.md の「ワーカー」節（now.md が無い task では research.md の末尾に同じ節）に `<agent 名> / session <id> / WS label / cwd / 動作中` の 1 行を書く。書いてから `herdr agent start <name> --kind <kind> --pane <root_pane> -- --session-id <id>` を実行する（claude 以外は `--` 以降を付けない）。kind は明示指定を優先し、無ければ現在の runtime kind。通常の harness 設定のまま、permission / trust の緩和を渡さない。`pane read --source visible` で composer を肯定確認し、trust 画面なら `blocked` として workspace / pane ID を人間へ示す。
6. 初期 prompt を一時ファイルに書き、`herdr agent prompt "$pane" "$(cat -- "$prompt_file")"` で `--wait` なしに投入する。本文は `dispatch: <dir>/brief.md を読み、あなたが元 Main から作業を受けた dispatch 先であることを確認して着手してください。最初の報告は <dir>/report-1.md に書いてください。` とする。`agent_prompt_stalled` では `pane read` で投入痕跡を確認するまで再送しない。
7. 待機は元の対話を塞がない runtime の background 待機で行う（Claude は Bash `run_in_background` の until ループ）。background 待機が無い runtime では、待機中は元の対話が塞がると人間へ伝える。`herdr-delegate check-marker --path <dir>/report-<n>.md` が 0、`herdr agent get <pane> | jq -r .result.agent.agent_status` が `blocked`、マーカーが無いまま `done` / `idle` が 3 回続く（例 15 秒間隔）、または上限時間（既定 60 分）のいずれかで抜ける。`done` / `idle` だけでは完了扱いにしない。マーカー以外で抜けたら `pane read --source visible` の要点と workspace / pane ID を人間へ示す。`blocked` には自動応答しない。
8. 報告を読み、1 行目の `kind` で分岐する。`question` / `approval` は人間へ提示し、回答を `reply-<n>.md` に書く。人間の承認・判断は「人間の発言（原文）」節に原文のまま置き、元の補足と区別する。`approval` の reply には報告の `presentation_id` を書く。先の `agent_status` が idle 系で composer を肯定確認できた時だけ `reply: <dir>/reply-<n>.md を読んで続行し、次の報告は <dir>/report-<n+1>.md に書いてください。` を投入し、7 へ戻る。`done` は成果物を diff・テスト結果などの一次証拠で確かめてから統合する。
9. close は `herdr-audit --age 0 --json` の該当 workspace で判定する。`dirty:*` があれば `git status --porcelain` を `baseline-status.txt` と比べ、先が増やした変更がある時は閉じずに報告する。`run:` が agent pane の数を超える時も閉じずに報告する。`unpushed:*` / `no-upstream` は branch と worktree path を報告に残して閉じてよい。先が報告した worktree の WS も、元が `workspace rename` で `<親 label>/dp:<slug>-wt` に付け直し、その worktree の `git status` で同じ判定をしてから閉じる。`herdr workspace close <workspace_id>` を実行し、連絡用 directory は残す。閉じたらワーカー節の該当行を `閉じた` にする。連絡用 directory が消えていて `baseline-status.txt` と比べられない時は、先の cwd と先が報告した worktree で `git status --porcelain` を見て、未 commit の変更があれば閉じずに報告する。
10. 元が再開された時（デスクからの再開、マシンの再起動の後）は、ワーカー節の `動作中` の行ごとに次を行う（session id のある claude の行だけ。それ以外は画面と workspace ID を人間へ示す）。`herdr agent get <agent 名>` で生きていればそのまま 7 から続ける。居なければ、同じ label・cwd で 4 の workspace を作り、`herdr agent start <agent 名> --kind claude --pane <root_pane> -- --resume <session id>` で同じ会話を起動し直す。連絡用 directory が無ければ作り直し、`再開: 元が再開しました。次の報告は <dir>/report-<n>.md に書いてください。` を投入して 7 へ戻る（`<n>` は元が最後に読んだ番号 + 1）。ワーカー節に無いワーカーは起動しない。
11. 人間が先を引き取ると言ったら、先の composer を確認して `takeover: 所有は人間へ移りました。brief の報告・中継の制約を解除し、以後は人間と直接対話してください。` を投入し、以後は回収・close しない。

報告形式（`brief.md` に書く）:

- 区切り（完了・質問・承認が必要・blocker）ごとに指定された `report-<n>.md` を書き、ターンを終える。
- 1 行目は `kind: done` / `kind: question` / `kind: approval` / `kind: blocked` のいずれか。本文は結論、変更場所（absolute path / branch）、実行した検証と結果、未了。質問は選択肢 2〜3 個と推奨を添える。`approval` には `human_review.py` の最新 `presentation_id` と提示内容（変更挙動・証跡・残余リスク）を書く。
- 中継された承認を記録する時は `user_citation` を `{role: "user", reference: "<親 workspace/pane ID>:<reply-n.md の絶対 path>", quote: <「人間の発言（原文）」の文言>}` とする。reply の `presentation_id` が最新の提示と違えば記録せず、再提示して `approval` を報告し直す。
- 書き終えてから最終行に `<!-- DELEGATE-COMPLETE -->` を置く。

## 既存 mode 共通のルール（`human-task` / `dispatch` には適用しない）

以下は既存の `agent` / `command:*` 用であり、`human-task` / `dispatch` は専用経路だけを使う。

- ペイン確保は `herdr pane split --current --direction <geometry> --cwd <呼び出し元が渡した絶対パス> --no-focus`。`$PWD` を既定にしない。ID は `.result.pane.pane_id` から取る（`parse-pane` サブコマンドでパースする）。
- geometry は `herdr pane layout` で決める。過密で最小幅を割るなら分割せず fail-soft する（狭いペインは screen 検出を劣化させ `unknown` を誘発する）。
- **`--no-focus` を守り、`agent focus` / `pane focus` を使わない。** `focus` 系コマンドは `done` を seen 扱いにしてしまい、workspace をまたぐ move で pane ID が変わる。
- **非 idle 中の画面取得は `pane read <pane_id> --source visible`。** `agent read` は非 idle 中 `agent_not_idle` を返すが `pane read` は状態非依存に読める。
- 一時ファイルの生成は Write tool か `<<'EOF'`（クォート済みデリミタ）でのみ行う。変数展開のあるリダイレクト（`echo "…" >`、クォート無しヒアドキュメント）は書き込み時点で展開・実行されるため使わない。
- 片付けは自分が起動した agent 名 / 記録した pane ID だけを対象にする。ID 失効時（ユーザーが手で閉じた・別 workspace へ移した）の close 失敗は無視し、fail-soft 経路を巻き添えにしない。`pane close` に `--force` 相当は無いため、失敗時はユーザーへ pane ID を提示して終える。
- **孤児回収**: 起動時に `herdr agent list` と `delegations.json` を `select-orphans --agent-list-json - --records <path> --current-generation N` に通す。`state == "held"`（`blocked` 残置・resident）、`mode != "agent"`、`generation >= 現世代` を除外し、**前世代の active な agent モードだけ**を回収対象にする。ユーザーや他 skill のペインには触れない。出力される agent 名を `delegations.json` で pane_id に引き直してから close する（close の対象は常に pane ID）。

## 隔離方針（`agent` モード専用）

`agent` モードの委譲先は、リポジトリではなくレビュー用 scratch ディレクトリを cwd として起動する。scratch は `herdr-delegate prepare-scratch` が確保する（自前の `mktemp -d` を使わない）。

```
<scratch>/
├── input/      ← spec / diff / plan をコピーして置く
└── out/<name>.md  ← 回収先
```

- **scratch root は固定・git 化・trusted 登録済みにする。** 既定は `${XDG_STATE_HOME:-~/.local/state}/herdr-delegate/scratch`（`HERDR_DELEGATE_SCRATCH_ROOT` で上書き可）。`prepare-scratch` が root を `git init` し、`$CODEX_HOME/config.toml`（既定 `~/.codex/config.toml`）へ `[projects."<root>"] trust_level = "trusted"` を 1 度だけ append し、その配下にユニークな scratch（`input/` と `out/` 付き）を作って絶対 path を返す。codex は cwd の git root に対して trust を解決するため、これで毎回の trust ダイアログが消える（P19）。追記は append-only で、既存表が `trusted` 以外なら書き換えず非ゼロ終了する（同名テーブルの重複は config を壊すため）。7 日より古い取り残し scratch は同時に掃除する。
- 隔離は **permission profile による default-deny** で作る。**`--sandbox` フラグは渡さない**（渡すと profile 自体が無効化され、`workspace-write` に落ちて read が全 FS へ素通りする）。読み取り許可は `":minimal"` とツールチェイン root（`command -v codex` の解決先を `build-launch-args` が導出する）の 2 つに限り、`<scratch>` にだけ write を与える。deny glob（`"**"="deny"` 等）は**使わない**。`bwrap` は最大引数数 9000 を超えると `Exceeded maximum number of arguments` で全コマンドを起動不能にするため、default-deny + 許可列挙で組む。
- 許可 root の値をハードコードしない。`build-launch-args --scratch D --profile-name N [--repo-root R]` が `command -v` の戻りから解決して組み立て、解決結果が repo や `.aidocs/` の祖先になっていないか（および `$HOME` 等の広域 root でないか）を祖先ガードで検査する。ガードに違反したら非ゼロ終了する。
- **`agent start` の前に必ず `verify-profile --scratch D --profile-name N --repo-root R` を通し、0 を返した時だけ続行する（非ゼロなら agent を起動せず fail-soft）。** これは同一 profile・同一起動形の canary を `codex sandbox` でゼロクォータに 2 本打つ: **正**（`test -e <scratch>` → 見えるはずなので 0 を期待）と**負**（`test -e <repo 直下に実在するエントリ（名前昇順の先頭）>` → 不可視のはずなので非ゼロを期待。特定のファイル名に依存させないのは、その名前が無い repo で「不在」を「不可視」と誤読して fail-open するのを避けるため）。**両方が期待どおりの時だけ 0** を返し、判定は終了コードのみで行う（メッセージ文字列を見ない）。正を併せて打つのは、負だけでは「隔離成立」と「canary がそもそも起動できていない」を区別できないため — `--permission-profile` を持たない codex（v0.129 未満）はパースエラーで非ゼロ終了するので、負だけの判定では**隔離ゼロのまま fail-open** する。この 2 本立てが version gate と `bwrap` 起動失敗の検出を兼ねる。
- **隔離が及ぶのはモデルが起動する子プロセスだけ**で、codex プロセス自身の会話ログ（`~/.codex/history.jsonl`、session rollout、sqlite）は sandbox 外に書かれる。scratch を削除しても、渡した入力は codex 側に残る。「書き込めるのは scratch のみ」はモデルが実行するコマンドについての主張であり、codex プロセス自体の永続化には及ばない。

## `agent` モードの手順

1. `command -v codex` で事前確認し、絶対 path を解決して保持する（PATH に無いと `agent start` は 30 秒 timeout する）。無ければ即 fail-soft。**この確認は controller の cwd で行うため委譲先の cwd（scratch）での可用性は保証しない**。scratch を cwd にすると mise が別バージョンの node を選び `codex` が PATH から消えることがある。
2. `herdr-delegate prepare-scratch` で scratch を確保し（trusted root 配下・`input/` と `out/` 込み）、入力を `<scratch>/input/` へコピーする。非ゼロ終了なら agent を起動せず fail-soft とする。
3. `build-launch-args --scratch <scratch> --profile-name <name> --repo-root <repo> --env-out <f>` で、`agent start` の `--` 以降に渡す argv（1 行 1 引数）と、次の手順で使う `--env` の値を得る。`--env-out` が書き出すのは展開済みの完成値なので、`PATH=…` を手で組み立てない。
4. `herdr pane split --cwd <scratch> --env "$(cat <f>)" --no-focus` でペインを確保する。**`--env` は必須**で、省くと手順 1 の false positive のまま `agent start` が 30 秒 timeout する。`pane read --source visible` で shell プロンプト到達を確認する（zsh + Zinit + mise で起動が遅い）。
5. `verify-profile` を実行する。**0 を返した時だけ続行し、非ゼロなら agent を起動せず fail-soft**（隔離が効いていない、codex が古い、または canary 自体が起動できない）。
6. `herdr agent start hd-<8hex>-<role>-<gen> --kind codex --pane <pane_id> -- <build-launch-args の出力>`（`-c "permissions.<name>={…}"` `-c 'default_permissions="<name>"'` `-c approval_policy="never"` `-c model_reasoning_effort="high"` `-c 'model="gpt-6-sol"'`）。起動する codex の model は `gpt-6-sol`、reasoning effort は `high` に固定（`~/.codex/config.toml` の既定は変えない）。`build-launch-args` の各出力行は single quote で包んで渡す（出力に `'` と改行が含まれないことを helper が保証している）。`approval_policy="never"` は default-deny 下で codex が権限昇格を要求して承認画面（＝ `blocked` 終端）に落ちるのを防ぐため。codex に `--effort` フラグは無い。**`--sandbox` は渡さない。**
   **argv の読み取りは `bash -c` で包む。** controller の shell は zsh で `mapfile` を持たないため、`mapfile -t ARGS < <(build-launch-args …)` は**空配列のまま非致命的に失敗し**、`agent start` は `argv: ["codex", ""]` で**成功してしまう**（＝ profile が渡らず隔離ゼロで起動する fail-open）。`verify-profile` は profile 定義が機能することしか見ないのでこれを検出しない。
   **起動直後に `agent start` の戻り JSON の `.argv` を検査し、`default_permissions="<name>"` を含むことを確認してから手順 7 へ進む。** 含まなければ prompt を投入せず pane を close して起動し直す。
7. **投入前ゲートは「状態 かつ 画面」の連言。** `agent get` が idle 系であることに加え、`pane read --source visible` で composer プロンプト（入力欄）を**肯定的に**確認できたときだけ投入する。確認できなければ画面内容・pane_id・到達手段を提示して停止する。`--wait` は承認画面で止まっていても `done` を返すことがあり、`blocked` / `unknown` の除外だけでは素通りするため。
8. prompt は `build-prompt --instruction-file F --input-dir <scratch>/input --output-path <scratch>/out/<name>.md` で組み立て、一時ファイルへ書いた上で `herdr agent prompt <pane_id> "$(cat "$f")" --wait` の形でのみ渡す。単一引数の上限は `MAX_ARG_STRLEN`（131072、`getconf ARG_MAX` の値ではない）で、100KiB を超える argv は分割せず fail-soft とする。
9. **完了判定の一次は `check-marker --path <scratch>/out/<name>.md` が 0 を返すこと**（ファイルが存在し、末尾に `<!-- DELEGATE-COMPLETE -->` を持つ）。herdr の状態は補助。マーカーが無い間は sleep-poll（例 5s × N）で待ち、上限で fail-soft とする。`agent wait` は `--until` 省略時に既に settled なら即返って busy-spin になるため一次判定には使わない。`--wait` / `agent wait` の戻りを単独の完了根拠にしない（`--wait` は turn を追跡せず、既に working 中なら別 turn の完了で満たされうる）。
10. `agent prompt` が `agent_prompt_stalled` を返した場合、**close / retry の前に `pane read --source visible` で投入痕跡を確認する**。`agent_prompt_stalled` は「投入後 5 秒以内に lifecycle 変化が観測できなかった」であり、本文は投入済みであることが多い。投入済みなら close / retry せず待機を続ける（二重投入とクォータ浪費を防ぐ）。
11. 回収した md の原本を `reviews/` に保存し、**kind / model / effort（`codex` / `gpt-6-sol` 等 / `high`）を evidence に残す**。scratch は回収後に削除する。

## `command` モードの手順

- **one-shot**: 呼び出し元が既に終了コードとログを保存する runner を持つ場合は再利用する。ない場合は `mktemp -d` などで今回専用の空 directory を確保し、その絶対 path を使って `herdr-delegate run-command --output-dir <directory> -- <command> <args...>` を対象 pane の cwd で実行する。引数は通常の shell quoting を行い、prompt や未検査の文字列をコマンドとして評価しない。helper は argv を shell=False で実行し、結合した stdout/stderr を pane と `output.log` へ流す。`run.json` の `state=finished` と実際の `returncode` を回収し、ログを確認した後にだけ close する。非ゼロは失敗、`failed` / `running` / ファイル欠落は成功にしない。再実行は新しい directory を使い、既存 run を上書きしない。
  `pane wait-output` は補助に留める。投入コマンド行のエコーや過去の出力にもマッチするため、完了や成功の一次証拠にしない。待機上限で結果がなければ未完了とし、投入済み command の状態を確認してから再試行する。`run-command` 自体は Herdr を呼ばないので、非 Herdr 経路でも同じ成果物を回収できる。これは実行結果の保存であり、workflow の正式な検証 receipt を代替しない。
- **resident**: `pane run` で常駐起動しペインを残したままターンを終える。停止は呼び出し元 skill の契約（ユーザー承認 → `send-keys ctrl+c` → close）に従い、この契約側から勝手に close しない。
- `command` モードの cwd は呼び出し元の作業ディレクトリ（worktree 等）でよい。scratch 隔離は `agent` モード固有。

## 終端状態

| 状態 | 扱い | ペイン |
|---|---|---|
| 正常完了 | 結果を返す | close |
| `blocked` | 第 3 の終端状態。`send-keys` で自動応答せず、画面内容・pane_id・到達手段（herdr サイドバーの attention queue / `prefix+o`）を提示して停止 | **残す**（`delegations.json` に `held` として記録） |
| `unknown` / その他の失敗 | 未完了として呼び出し元へ返す。任意経路は同等の非 Herdr 経路へ戻せる。必須 specialist / review / 隔離条件は省略せず、代替不能なら停止 | 自分の所有と実行状況を確認して扱う |

`unknown` は「分類できない」だけで承認 UI の証拠ではなく、狭いペインでも出るためユーザーを止める側に倒さない。

ただし、上記および本文の fail-soft は品質 gate の免除ではない。投入後の失敗は重複実行を避けるため現在の画面・成果物を確認する。`command:resident` は unknown / timeout でも勝手に停止・close せず、常駐の停止契約を維持する。

## 落とし穴と回避（実測・公式ドキュメント由来）

| # | 事実 | 契約側の回避 |
|---|---|---|
| P1 | `--wait` は承認画面で止まっていても `done` を返すことがある | 投入前ゲートを「状態 かつ 画面」の連言にする（手順 7） |
| P2 | `--wait` は turn を追跡しない | 完了判定の一次は終端マーカー付きファイル（手順 9） |
| P3 | `agent start` は trust / 承認画面が出ていても `interactive_ready: true` で返る（`--sandbox` の有無に関係しない。codex-cli 0.149.1 実測） | canary（`verify-profile`）で隔離を先に確認し、投入前は `pane read --source visible` で composer を肯定的に確認 |
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
| P18 | zsh に `mapfile` は無い。argv 配列が空のまま `agent start` が `argv: ["codex", ""]` で**成功**し、隔離ゼロで起動する（`verify-profile` は profile 定義しか見ないので検出できない）。実測で発生 | argv の読み取りを `bash -c` で包み、`agent start` の戻り `.argv` に `default_permissions` が含まれることを確認してから prompt 投入（手順 6） |
| P19 | codex は cwd（git 管理下なら git root）が `$CODEX_HOME/config.toml` の `projects` で `trust_level="trusted"` になっていない限り directory trust ダイアログを出す。cwd を毎回新規の `mktemp -d` にすると毎回聞かれ、ユーザーが承認するたび `/tmp/...` の trust 表が config に溜まる。`-c projects."<scratch>".trust_level="trusted"` の CLI override では抑止できず、scratch を `git init` しただけでも抑止できない（いずれも codex-cli 0.149.1 実測） | `prepare-scratch` が固定 scratch root を `git init` して 1 度だけ trusted 登録し、scratch をその配下に作る（実測で trust ダイアログ消失）。それでも trust 画面が出たら `blocked` の契約どおり `send-keys` で自動応答せず fail-soft とし、呼び出し元は Codex 無しで gate を成立させる |

## prompt 作法

- 委譲先が GPT 系なら `writing-gpt-prompts`、Claude 系なら `writing-claude-prompts` に従う。ただしこれらは**構成の指針であって言語の指針ではない**。
- **instruction-file 本文は日本語で書く。** 委譲先の出力も日本語で受け取る（技術名 / コマンド名 / API 名 / エラー文は原文のまま）。`build-prompt` が末尾に日本語出力の指定を付けるが、本文が英語だと委譲先はそれに引きずられるため、本文の言語も呼び出し元の責務とする。回収した md をそのままユーザーへ見せる前提で、翻訳の手戻りを作らない。
- **初回 prompt からファイル出力を指示する。** herdr 公式 skill（`dot_agents/skills/herdr/SKILL.md:185`）は "do not request file output in the initial prompt" としているが、本契約はこれを意図的に上書きする。根拠は 2 点: (a) alternate screen から出た行は host scrollback に入らず `--lines` を増やしても回収できない（P6）ため、初回から回避しないと出力を丸ごと失いうる、(b) 完了判定を状態非依存の終端マーカー付きファイルに載せるため（herdr の状態は補助）。呼び出し元 skill はこの上書きを再掲しない。

## timeout の 2 段構え

Task tool はターンをブロックするため、reviewer のレンズ並列が返るまで controller は Codex の状態を見に行けない。**Codex 側 `--wait` の timeout は reviewer 側の想定より短く取り**、Task 復帰直後に `agent get` / `check-marker` で取り直す。これにより、ブロックされている間に Codex 側が完了・停止していても、復帰後の 1 手で検知できる。
