---
name: open-slide
description: |
  Open the webinar slide (astro/dist/index.html) in the default browser.
  Cross-platform (macOS / Linux / Windows).
  Trigger: 「スライドを開いて」「資料を開いて」「ウェビナー」
user-invocable: true
---

# Open Slide

ビルド済みウェビナースライド（`astro/dist/index.html`）をデフォルトブラウザで開くスキル。macOS / Linux / Windows に対応。

## 処理フロー

### ステップ1: スクリプト実行

確認不要。即座に実行する。

```bash
python3 .claude/skills/open-slide/scripts/open_slide.py
```

### ステップ2: 結果報告

スクリプトの stdout をそのまま伝える。

## 重要な制約

- **軽量化**: サブエージェント・ファイル読み込み等の重い処理は行わない
- **追加の調査やファイル読み込みは一切行わない**
