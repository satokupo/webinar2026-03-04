# CLAUDE.md

## リポジトリ概要

ウェビナー「Claude Code グローバルスキル構成の紹介」の実物提供用リポジトリ。
参加者がクローンして `.claude/` 配下のスキル・フック・エージェント構成を実際に確認・動作させられる。
Astro 製スライド（ビルド済み）も内包している。

## プロジェクトルート

```
クローンしたルートディレクトリ
```

作業ディレクトリは常にこのパスを基点とすること。

## ディレクトリ構成

```
ウェビナー資料2026-03-04/
├── .claude/
│   ├── agents/        # カスタムエージェント定義
│   ├── hooks/         # フックスクリプト（Python）
│   ├── plans/         # プランファイル置き場（gitignore対象）
│   ├── rules/         # 条件付き自動ロードルール
│   ├── skills/        # スキル定義（11個）
│   ├── temp/          # 一時ファイル置き場（gitignore対象）
│   └── settings.json  # フック設定・プランディレクトリ設定
├── astro/             # ウェビナースライド（Astro 5 + Tailwind CSS 3）
│   ├── dist/          # ビルド済みスライド（配布用）
│   └── src/           # スライドソース
├── .gitignore
├── CLAUDE.md
├── LICENSE
└── README.md
```

## 技術スタック

- **Astro 5** + **Tailwind CSS 3** — スライド部分

## 運用ルール

- `plansDirectory`: `.claude/plans`（プランファイルの保存先）
- macOS 環境で作成。一部機能（効果音再生 `afplay`）は macOS 限定

## スキル・フック・エージェント一覧

### スキル（11個）

| スキル | 説明 |
|--------|------|
| `context-handover` | コンテキスト引き継ぎファイル生成 + /compact 送信 |
| `current-session-id` | 現在のセッションID取得 |
| `git-commit-rules` | Git コミットのルール・手順 |
| `omikuji` | 開発者おみくじ（今日の運勢） |
| `open-slide` | ウェビナースライドをブラウザで開く |
| `planmode-rules` | プランモードのワークフロー・検証 |
| `save-chatlog` | チャットログのMarkdown保存 |
| `skill-design-guide` | スキル設計ガイド・チェックリスト |
| `summon-experts` | 専門家パネルディスカッション |
| `tab-rename` | ターミナルタブ名変更 |
| `tab-reset` | タブを待機状態にリセット |

### エージェント（1個）

| エージェント | 説明 |
|-------------|------|
| `impl-checker` | プラン実装完了チェック |

### フック（3個）

| フック | タイミング | 説明 |
|--------|-----------|------|
| `precompact-handover` | PreCompact | コンパクション時に引き継ぎファイル自動生成 |
| `sessionstart-load-handover` | SessionStart (compact) | コンパクション後のセッション開始時に引き継ぎファイル読み込み |
| `send-continue` | PostToolUse (EnterPlanMode) | プランモード突入時に planmode-rules 読み込み指示 |

## 前提条件

- Claude Code CLI
- tmux（tab-rename / tab-reset / save-chatlog の一部機能）
- macOS（効果音再生機能）
