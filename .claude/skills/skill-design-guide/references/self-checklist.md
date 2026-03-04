# skill-design-guide 自己チェックリスト

> このチェックリストは skill-design-guide 自身を編集する際に使用する。
> 他のスキルをチェックする際は、anthropic-guidelines.md の「構造チェックリスト」を参照すること。

## 書き込み先の正当性
- [ ] 追加・変更する内容の情報源を確認したか（Anthropic公式 or ユーザー独自）
- [ ] Anthropic公式情報 → anthropic-guidelines.md に記載しているか
- [ ] ユーザー独自ルール → user-guidelines.md に記載しているか
- [ ] 情報源が不明な場合、ユーザーに確認したか

## 参照整合性
- [ ] ファイル名を変更した場合、SKILL.md 内の参照を更新したか
- [ ] ファイル名を変更した場合、他の references ファイル内の参照を更新したか
- [ ] 優先順位ルール（user-guidelines > anthropic-guidelines > ウェブ参照）との整合性は保たれているか

## コンテキスト効率
- [ ] SKILL.md に追加した内容は「常時必要な情報」か（不要なら references/ に分離）
- [ ] references/ の新規ファイルは SKILL.md から参照指示があるか（いつ・何を読むか明確か）
- [ ] SKILL.md のフロントマター抜き行数がuser-guidelinesの行数制限内か（推奨50行、許容100行、硬い上限150行）
- [ ] 実行詳細がreferences/に分離されているか（概要・絶対制約・ルーティング以外）
- [ ] references内のファイルに読み込み指示（「次は○○を読め」）が含まれていないか

## description
- [ ] descriptionは英語ベースで書かれているか
- [ ] 日本語はトリガーキーワードの引用のみか

## サンプルコード正確性
- [ ] コードブロック内のフロントマターキーが、本ファイル（anthropic-guidelines.md）のオプションフィールド一覧に存在するものだけか

## スキル間連携
- [ ] パス指定でのSKILL.MD Read方式を使っていないか
- [ ] 呼ばれる側のスキルに`user-invocable: false`が設定されているか（該当する場合）
