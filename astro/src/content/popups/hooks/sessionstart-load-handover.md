# sessionstart-load-handover（引き継ぎ読み込み）

## 何のためのフックか

コンパクション後のセッション再開時に、引き継ぎファイルを自動的に読み込む SessionStart フック。
precompact-handover や context-handover が生成したファイルを additionalContext として注入し、AIが文脈を復元できるようにする。

## やっていること

1. `.claude/temp/` から `{session_id}_handover.md`（スキル生成）と `{session_id}_autocompact.md`（フック生成）を探索
2. 見つかったファイルの内容を additionalContext として stdout に JSON 出力
3. 両方存在すれば結合（スキル生成を先頭に配置）
4. スキル生成の handover が存在し tmux 環境なら、send-continue.py をバックグラウンド起動

## 工夫したこと

- **2種類の引き継ぎファイルに対応**: スキルが生成する `_handover.md` とフックが生成する `_autocompact.md` の両方を探索・結合。どちらか一方だけでも、両方あっても動作する
- **フェイルオープン設計**: どちらのファイルも見つからなければ exit 0 で通常再開。引き継ぎがなくてもセッション自体は止まらない
- **send-continue との連携**: スキル生成の handover がある = ユーザーが意図的に圧縮した場合のみ自動続行プロセスを起動。autocompact のみの場合は起動しない（自動圧縮は意図的ではないため）
