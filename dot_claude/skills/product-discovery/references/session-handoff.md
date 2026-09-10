# session 引き継ぎ

phase 境界だけを理由に session を替えない。同じ controller が context と検証済み artifact を使って続ける。

`<context-size-warning>`、実際の context 欠落、またはユーザーの中断希望がある時だけ `handoff` skill を提案する。次 phase の案内と同じ応答で理由と再開用 artifact path を短く示し、不要なら続行できると伝える。spec の議論を保持したい場合は compact、それ以外は new-session を候補にする。

- ユーザーが断った場合（応じずに続行を指示した場合も含む）は、その session で繰り返さない。
- ユーザーが応じるまで `handoff` を起動せず、引き継ぎ md を先に作らない。
- short path、`execute-and-ship` の内部境界、cleanup の終端では phase だけを理由に提案しない。
- `warn-context-size.sh` の警告機構は変更しない。既存 workflow の `context.json` が state authority であり、再開は最初の未完了 gate から行う。
