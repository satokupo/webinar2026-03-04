---
name: planmode-rules
description: |
  Rules and workflows for plan mode, including Phase 5 Codex validation.
  Reference when creating, reviewing, or validating plans.
  Trigger: 「プラン作成」「planmode-rules」
user-invocable: false
---

# プランモード ルール

## 基本原則
- ユーザーが明示的に「書き換えて」と指示した場合を除き、確認なしにプランファイルを書き換えない
- このスキルの責任範囲はプランの作成・検証までであり、プラン実行後のセッションには影響を及ぼせない。実行後に必要な指示はプラン本文内に記述すること

## 前提条件チェック（スキル読み込み時に毎回実行）
1. 現在プランモードか確認する
2. プランモードでなければ `EnterPlanMode` を呼び出す（ユーザー承認ダイアログが表示される）
3. プランモード確認後、以下のフロー分岐に進む

## フロー分岐

ユーザーの発言に応じて、読み込むドキュメントを切り替える。

| トリガー | 読み込むドキュメント | 備考 |
|---------|-------------------|------|
| プラン作成・ブレスト開始 | `references/planning-flow.md` | Phase 1-3 |
| 「検証準備」「検証して」 | `references/validation-flow.md` | Phase 4 初回検証 |
| 「完璧ですか？」 | `references/validation-flow.md` | Phase 4 中断後の再開 |
| 「CODEX検証」 | `references/codex-review-flow.md` | Phase 5 CODEX検証 |

**重要**: 各トリガー時は対応するドキュメントのみを読み込む。他のフロードキュメントは読み込まない（コンテキスト節約のため）。

## 一時ファイルの管理

検証フロー（Phase 4-5）で生成される一時ファイルはプロジェクトローカルの `.claude/temp/` に `{session_id}_種別.md` のプレフィックス方式で保存される。

- **対象ファイル**: `{session_id}_conversation.md`, `{session_id}_handover.md`（スキル生成の引き継ぎファイル: context-handover）, `{session_id}_autocompact.md`（PreCompact フック自動生成のコンパクション記録）, `{session_id}_codex-review.md` 等
- **クリーンアップ**: 検証完了後も自動削除しない。`save-chatlog` スキルでチャットログ保存時に `{session_id}_` プレフィックスマッチで一括自動削除される
- **並列安全性**: セッションIDがファイル名プレフィックスに含まれるため、複数セッション・複数リポジトリでの並列検証に対応
