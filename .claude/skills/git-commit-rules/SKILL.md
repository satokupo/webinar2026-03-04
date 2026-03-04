---
name: commit
description: |
  Rules for git commits: message format, confirmation flow, and push procedures.
  Reference this when committing changes or after completing plan execution.
  Trigger: 「コミット」「コミットして」「pushして」
user-invocable: true
---

# Git コミットルール

コミット時のメッセージ形式、確認フロー、pushルールの Single Source of Truth。

## コミットメッセージ形式

- **言語**: 日本語で作成する
- **1行目**: プレフィックス付きの簡潔なタイトル（例: `feat:`, `fix:`, `docs:`, `refactor:`）
- **2行目以降**: リスト形式で変更内容の説明

## コミットフロー

`references/commit-flow.md` を読み込み、Phase 1〜4 を実行する。
コミット対象が文脈から明確な場合（プラン実行後等）と不明確な場合（`/commit` のみで呼び出し等）で Phase 1 の手順が分岐する。

## push ルール

- **リモート判定**: `git remote` の出力でリモートの有無を判定する。リモート未設定の場合は push をスキップし、その旨を表示する
- **push はチャットで確認しない** — settings.json の ask ルールでシステム側が確認するため
- **git push は必ず別コマンドで実行する**（`&&` で連結しない）— settings.json の ask ルールが `&&` 連結コマンドでは発動しないため
