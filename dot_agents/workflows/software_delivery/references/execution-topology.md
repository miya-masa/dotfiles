# 実行先の選択

目的は、ユーザーが一つの目的を渡した後、実行先の細部を毎回選ばずに済むこと。通常は Main Agent が統合担当となり、必要な能力・隔離・観測手段を満たす最小の構成を選ぶ。人間所有の別 task は下記の `human-task` 経路で扱う。role / model / effort は [effort-policy.md](effort-policy.md)、review の独立性と人数は runtime の review policy を正本とする。実行先の変更で権限、承認、品質条件を変えない。active runtime の委譲制約が優先する。

## 選択する軸

まず作業の依存と owned paths を確認する。独立して進む仕事、または独立した専門判断がなければ分岐しない。委譲の利益を、説明・起動・待機・結果回収・裏取りの費用と比べる。長さだけで agent を増やさず、既存 context が効く逐次作業は同じ担当で継続する。

| 実行先 | 選ぶ条件 | 制約と回収 |
| --- | --- | --- |
| Main Agent 直接 | 明確な局所作業、読む先が決まった探索、統合、コマンド実行 | 長時間待つだけなら追加の推論 agent は不要 |
| built-in sub-agent | bounded な探索・実装・仕様判断・fresh review。会話内で結果を回収でき、独立 context の利益がある | filesystem が分離されるとは限らない。parallel write は別 worktree・共有ファイルなし・順序依存なしが必要 |
| Herdr pane | 人間が途中経過を見たいテスト・監視・常駐コマンド、既存の明示クロスモデルレビュー | pane は端末の隔離。branch / filesystem / permission の隔離ではない。下記 backend 契約を使う |
| Herdr workspace | 既に必要と判断した別 worktree、長く独立して維持・再開する作業の表示単位 | workspace を作るだけでは worktree は分離しない。既存 worktrunk hook が開く場合は追加作成しない |
| 人間所有の別 task (`human-task`) | 指定された別作業を人間と新 Main が後で引き継ぐ準備 | Herdr 内は新 workspace と新 Main。Herdr 外は同じ handoff file と prompt を返し、built-in へ置換しない |
| 外部 agent / 別モデル | 必須の専門能力が現在の runtime にない、または明示クロスモデル確認 | モデル選択と transport は別。入力共有範囲・実効権限・結果回収を確認できる既存経路だけ使い、remote 転送を暗黙に認可しない |
| 人間 | 目的・scope・保護対象の未決、承認 UI、必要な権限 | pane と sub-agent の日常的選択は Main Agent が引き受ける |

context isolation と filesystem isolation は別に扱う。review は作成会話を継承せず、成果物と AC・一次証拠から開始する。別モデル・別 pane だけでは独立 review は成立しない。同じ cwd の worker を増やしても競合は減らない。

## backend の境界

- 標準は runtime の直接 tool / built-in sub-agent。Herdr が存在するだけでは追加 worker / reviewer を作らない。
- Herdr を使わないという指定があれば全経路で尊重する。Herdr 候補時だけ `herdr-delegate check-availability` を使う。`eligible=false` または helper 不在なら非 Herdr 経路へ進む。`eligible=true` は環境変数と executable の存在だけであり、server 接続・起動許可・モデル可用性・隔離成立を保証しない。
- 実際の Herdr 操作は [herdr-delegate](../../../skills/herdr-delegate/SKILL.md) の対応 mode へ渡す。CLI 手順を task / phase / prompt に複製しない。`HERDR_ENV` を偽装して外側からユーザーの session に接続しない。
- 現在対応する mode は `command:one-shot`、`command:resident`、既存の scratch 隔離された Codex クロスモデルレビュー `agent`、人間所有の別 task 用 `human-task`。`agent` の Sol/high 固定・レビュー用 read 範囲を汎用実装workerや `human-task` に流用しない。通常の実装・必須 specialist は対応する built-in 経路へ渡す。
- `human-task` 以外で Herdr workspace が必要なら既存 worktree / park 契約を使う。`human-task` は下記専用手順で表示用 workspace を作るが、新しい workspace lifecycle、台帳、scheduler は作らない。Herdr がなくても worktree と証拠を使って再開できる状態にする。

## 人間所有の別 task (`human-task`)

次の文言または同じ意図を示す trigger に限りこの経路を使う: 「別作業にして後で自分」「別WSで準備」「別作業にして進めて」。別作業という語だけで判定せず、人間へ引き渡す意図がある場合に限る。結果の回収・統合も現 Main に任せる指示なら通常委譲を優先する。ユーザーの永続運用指定があるため、毎回 Herdr 指示や workspace 作成を確認しない。

- Herdr 内では新しい workspace と、現在の runtime kind の新 Main を作る。kind の明示指定があれば優先する。Herdr を使わない／使えない場合は同じ handoff file と初期 prompt だけを渡し、built-in agent へ置換しない。
- 現在 Main は現在の目的を維持し、引き渡しの統合は人間と新 Main が担う。旧 Main は引き渡した新 WS / agent を自動回収・close しない。worker / reviewer はこの経路を使わず Main だけが起動する。
- 新 Main の委譲は一段までとし、別 task の root を無限に増やさない。
- 既定は `prepare-only`: handoff 本文と適用指示を読み、短い受領確認だけ返す。task 分類、workflow、編集、実行、再委譲を始めず、人間の GO を待つ。同じ依頼に「着手して」「実装も進めて」など実行開始の明示指示（`start`）がある場合だけ既存 task を開始し、phase の承認を維持する。作業別 skill は作らず既存 task を使う。
- handoff file は既存 `/tmp` scratch に一回だけ保存し、目的、元依頼原文の範囲、prepare / start、absolute cwd / branch、background / evidence / unknown、non-goal / 権限、次の一手、現在 source と別 task の所有者を含める。親 workflow context を新 session で resume / update せず、親 dirty をコピー・自動適用しない。
- 新 worktree は `human-task` 自身で作らず、GO / start 後の既存 task が必要性と gate を判断する。初期 prompt は新 Main 自身が引用された別作業化依頼を再実行して新 WS / agent を作らないよう指示する。

## 所有者と深さ

一つの目的につき Main Agent が task 分解、worker 作成、回収、採否、最終検証を所有する。worker / reviewer は再委譲せず、必要なら理由と未解決事項を Main Agent へ返す。既定の委譲深さは Main → worker の一段。これは指示上の制約であり、runtime の機械的な深さ制限が有効だと主張しない。

spawn packet に既存の必須項目とともに統合担当、owned paths / cwd、再委譲禁止、成果物、停止条件を含める。指定 model / effort と観測できた実効値を区別する。割り当てた役割が満たせない時に軽いモデルや直接作業へ黙って置換しない。

## 見える進行と失敗

分岐前に「担当・仕事・理由・実行先・回収条件」を短く伝える。実行中は backend の ID、cwd / worktree、状態、待ち理由、成果物の場所を既存の進捗記録へ追記する。新しい恒久台帳は不要。Herdr agent 名は既存 `hd-<8hex>-<role>-<gen>`、command pane の補助ラベルは短い `test-<task>` / `watch-<task>` などを使う。label は所有権の証明ではない。

Herdr の `done/idle`、process 終了、task 検証成功を区別する。`blocked` は内容と到達先を伝え、承認を自動入力しない。timeout / unknown は成功にせず、投入済みの仕事を確認してから再試行する。任意の表示 backend が使えなければ同等の直接実行へ戻せるが、必須 review / 隔離 / specialist の失敗はその条件を維持できる代替か停止にする。

常駐・外部待ちをターン後も残す場合は所有者と停止方法を報告する。session を閉じて後で戻る場合は既存 `park` に待ち条件・外部影響・再開情報を渡す。閉じる対象は自分が作ったものだけとし、ユーザーの既存 pane を回収対象にしない。
