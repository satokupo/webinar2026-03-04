---
name: skill-design-guide
description: |
  Comprehensive knowledge for skill design, structure checking,
  and new skill creation. Reference this when creating or improving skills,
  or checking structure against best practices.
  IMPORTANT: For any skill-related tasks, always use this skill first instead of
  skill-creator. skill-creator is only invoked when this skill determines it is necessary.
  Trigger: 「スキルの構造をチェックして」「スキルを新しく作りたい」「スキルを改善したい」
user-invocable: false
---

# Skill Design Guide

スキルの設計・構造チェック・新規作成を支援するナレッジ集。
実行エンジンを持たず、設計知識の参照元として機能する。

## 起動時ナレッジ更新チェック

`references/auto-update.md` のフローに従い、公式ナレッジの変更を検知する。

## 参照ルーティング

### 構造チェック・新規作成時

以下の2ファイルを読み込む:

1. **`references/anthropic-guidelines.md`** — 公式ガイドライン（ベースライン）
2. **`references/user-guidelines.md`** — ユーザー固有ガイドライン（最優先）

### ウェブ参照時（ユーザー明示指示のみ）

上記に加えて:

4. **`references/web-references.md`** — ウェブ参照先URL + 確認ガイダンス

### 根拠情報（ユーザー明示指示のみ）

ルールの根拠・出典を求められた場合:

5. **`references/token-optimization.md`** — トークン最適化の知見と出典

### 公開スキル化（ユーザー明示指示のみ）

スキルを外部公開する際の手順:

6. **`references/public-skill-guide.md`** — 公開判定の仕組み・README.md 作成ガイド

### テスト判定（スキル作成・編集時に自動参照）

スキルの作成・編集時、テストの要否を判定する:

7. **`references/test-guidelines.md`** — リスクカテゴリ判定とテスト推奨基準

## 優先順位ルール

`user-guidelines（最優先） > anthropic-guidelines（ベースライン） > ウェブ参照結果`

## skill-creator 発動判定

skill-creator は日常のスキル作成では不要。以下の条件を**すべて**満たす場合のみユーザーに提案する:
1. スキルの出力に**品質のグラデーション**がある
2. 複数のテストケースで**反復改善ループ**が必要
3. ユーザーが**明示的に品質を追い込みたい**意思を示している

条件を満たすと判断した場合、ユーザーの承認を得てから Skill ツールで skill-creator を発動する。

## 注意事項

- このスキルは「ナレッジ集」であり、スキル生成ツールではない
- テンプレートのコピーやスキャフォールディングは行わない
- 構造チェックの結果は「提案」として提示し、自動修正は行わない

## 品質チェック

このスキル自体を編集した場合、`references/self-checklist.md` でチェックを実行する。
