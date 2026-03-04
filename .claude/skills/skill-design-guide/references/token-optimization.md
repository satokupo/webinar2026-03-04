# トークン最適化の知見

Xポスト・Zenn記事から得たClaude Codeスキルのトークン消費に関する知見集。
user-guidelines.md の行数制限やファイル分離ルールの根拠資料として位置づける。

> **注意**: これらはコミュニティの実測・検証に基づく知見であり、Anthropic公式ドキュメントには記載されていない内部挙動を含む。将来のアップデートで変更される可能性がある。

---

## コンパクト後リロード問題

- **事象**: 一度でも呼ばれたスキルのSKILL.MDが、コンパクション後に全文リロードされ続ける
- **出典**: kei31氏のXポスト（実測に基づく報告）
- **ステータス**: 公式未文書化の内部挙動。将来変更される可能性あり
- **対策**: SKILL.MDの行数を最小化し、実行詳細はreferences/に分離する
- **補足**: kei31氏は「SKILL.MDを一文にしてinstruction.mdを読ませる」極端な方式を採用。パネルディスカッションで検討した結果、概要・制約が消えるとルーティング精度低下のリスクがあるため、適度なバランス（推奨50行/許容100行/硬い上限150行）を採用

---

## スキル間ネストのキャッシュ破壊

- **メカニズム**: Claude Codeは16トークンブロック単位でハッシュチェーンを構成し、コンテキストキャッシュを管理している。Skillツールでのスキル間ネスト呼び出しにより途中ブロックが変わると、チェーン全体のキャッシュが破壊される
- **影響**: ネスト方式は展開形式と比較して1.7〜3.1倍のトークン消費
  - 基礎テスト: 3.1倍
  - Git関連テスト: 1.7倍
- **出典**: yossulito氏のZenn記事（実測データ付き）
- **対策**: スキル間連携が必要な場合は、ビルトイン変数置換や機能コピーを優先し、Skillツールでのネスト呼び出しは最終手段とする

---

## スキル内ファイルネスト（区別）

スキル間ネストとは異なるメカニズム。同一スキル内でreferences/のファイルをRead連鎖する場合:

- キャッシュ破壊の影響は小さい（同一コンテキスト内のRead操作のため）
- 主なリスクはLLMの指示追従信頼性: references内に「次は○○を読め」と書いても見落とされる可能性がある
- **対策**: ファイル読み込み制御はSKILL.MDに一元化。references内には読み込み指示を書かない

---

## description常駐コスト

- 全スキルのdescriptionが**常時**コンテキストウィンドウに存在する
- budget: コンテキストウィンドウの2%（フォールバック16,000文字）
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 環境変数で上書き可能
- スキル数が多すぎるとbudget超過で一部スキルのdescriptionが除外される
- **対策**: descriptionは英語で簡潔に書く（日本語はトークン効率が悪い）

---

## 出典

### Zenn記事
- https://zenn.dev/studist/articles/03-skill-nesting-vs-expansion
- https://zenn.dev/studist/articles/05-why-skill-nesting-hurts-cache

### Xポスト（主要3名）
- kei31氏: https://x.com/kei31/status/2023506553060606046 （コンパクト後リロードの実測）
- kei31氏: https://x.com/kei31/status/2023533001158934776
- yossulito氏: https://x.com/yossulito/status/2023414014769050106 （スキルネストのトークン消費）
- yossulito氏: https://x.com/yossulito/status/2023415887022465503
- yossulito氏: https://x.com/yossulito/status/2023670239653749209
- grandchildrice氏: https://x.com/grandchildrice/status/2023386681039266149 （トークン消費の異常増加）
- grandchildrice氏: https://x.com/grandchildrice/status/2023415002229784685
- grandchildrice氏: https://x.com/grandchildrice/status/2023575031620477168
