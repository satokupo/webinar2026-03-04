# summon-experts（専門家召喚）

## 概要

何かしらの議題に対して、テーマに関連するロールの専門家を3〜5体呼び出し、キャラクター付きでパネルディスカッションさせるスキル。
議論の過程が目に見える形でチャットに残っていく。

用途は開発に限らず、自分があまり詳しくない分野の壁打ち、立案した内容の妥当性チェック、穴探しなど幅広く使える。

ディスカッション後、プラン作成に入る場合は planmode-rules と連携する構造。
ディスカッションにユーザーが口を挟む場合の発言の重みは他のパネリストとフラット。

---

## 内部フロー

### Phase 1: 課題分析と専門家ロール提案

ユーザーが「これについて話したい」と言ったり、それまでのチャットのやり取りから、まず大まかな流れを把握するフェーズ。

```
入力: それまでのチャットのやり取り
  ↓
処理: 議題をYAML形式で構造化（概要・背景・論点・ゴール）
  ↓
出力: 課題YAML + 専門家ロール提案テーブル（役職名・召喚理由）
  ↓
→ ユーザー承認を待つ（修正指示があれば反映）
```

---

### Phase 2: フルキャラクター設定の展開

承認された各専門家に、深いキャラクター背景を付与する。
具体的な経歴・視点の傾向・議論での立ち位置（推進派/慎重派/バランサー等）を設定し、議論の説得力を高める。

```
入力: Phase 1 で承認された専門家リスト
  ↓
処理: 各専門家のキャラクター設定を生成・表示
  ↓
連携: tab-rename スキルを発動 → 課題テーマでタブ名を自動設定
  ↓
→ ユーザー承認を待つ
```

**関連スキル**: [tab-rename](../サブスキル/tab-rename.md)（タブ名の自動設定）

---

### Phase 3: パネルディスカッション

全議題を**1ターンで自動進行**する。ユーザーに質問を挟まず最後まで走破するのが基本方針。

```
入力: 課題YAMLの論点 → 議題リスト
  ↓
ループ（各議題ごと）:
  1. separator.py を実行（出力のフラッシュポイント）
  2. 議題見出しを罫線付きで表示
  3. 各専門家が自分の専門領域の視点から発言
  4. まとめ（暫定結論 + 事実確認状況）を引用ブロックで表示
  ↓
→ 全議題完了後、Phase 4 へ
```

---

### Phase 4: 最終提案

全議題の議論結果を集約し、実装可能な推奨アクションをまとめる。

```
入力: Phase 3 の全議題の暫定結論
  ↓
Step 1: 最終確認事項の提示
  - 専門家間で意見が分かれた項目
  - ユーザー確認が必要だが自動進行で飛ばした項目
  - ベストプラクティスからの乖離で承認が未確認の項目
  → ユーザー確認を待つ
  ↓
Step 2: 最終提案の提示
  - 問題の要約
  - 推奨アクション（理由付き）
  - リスク・留意点
  - 合意に至らなかった点
  - 未解消の課題 → 該当あればログファイル作成
  - 要望充足の確認（元の要望 vs 推奨アクションの因果関係）
  ↓
Step 3: 次アクションの選択（AskUserQuestion）
  選択肢:
    1. 合意形成YAMLを作成してからプラン作成（推奨）
    2. コンテキストを圧縮してからプラン作成
    3. 直接プラン作成
  ↓
→ planmode-rules スキルを発動
```

**関連スキル**: [planmode-rules](02_planmode-rules.md)（プラン作成フェーズへ接続）

---

## フロー全体図

```
Phase 1          Phase 2          Phase 3              Phase 4
課題分析     →   キャラ設定   →   パネルディスカッション → 最終提案
 ↕ユーザー承認    ↕ユーザー承認    自動進行               ↕ユーザー確認
                 tab-rename発動   separator.py            ↓
                                  事実調査(Sonnet)     planmode-rules へ
```

---

## このスキルで工夫したポイント

<div style="padding: 0 56px; display: flex; flex-direction: column; gap: 16px;">

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; color: #374151; border-bottom: 1px solid #e2e8f0; background: #dbeafe; color: #1d4ed8;">ユーザー意見のフラット化</h3>
<div style="padding: 12px 20px 16px;">

LLMはユーザーの意見にそのまま同意しがち（sycophancy）。「同意するな」程度の消極的な禁止では対抗できないため、**構造的なプロトコル**で対処している。

ユーザーの発言は「議論への追加インプット」として、**他のパネリストの発言と同等の重み**で扱う。
ユーザーが方針・設計に関する意見を述べた場合、以下の4ステップが強制的に走る:

1. **受け止め** — ユーザーの意見を理解したことを示す
2. **ベストプラクティスとの照合** — 乖離があれば具体的に指摘。乖離がなくても照合したことを明示する（**省略禁止**）
3. **影響分析** — 仮に採用した場合のリスク・矛盾・波及範囲を分析
4. **専門家間ディスカッション** — 上記を踏まえて批判的に検証

ユーザーが再度主張した場合は「ベストプラクティスから外れることを承知の上での決定」として受け入れ、記録して進行する。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; color: #374151; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">事実確認の相互検証</h3>
<div style="padding: 12px 20px 16px;">

調べれば分かることを推測で答えてしまうのはLLMのよくある問題。
これを**ルールで禁止する**のではなく、**会話の流れとして制御する**設計にしている。

専門家が推測表現（「〜はず」「おそらく」等）を使うと、別の専門家が「それは調べた方がいいよね」と提案する。
自分が出した発言に縛られる性質を利用して、「調べましょう」という流れが自然にできる。
調査は WebSearch（軽い確認）または Sonnet サブエージェント（精読が必要な場合）で実施。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; color: #374151; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">矛盾・課題の先送り禁止</h3>
<div style="padding: 12px 20px 16px;">

議論中にスコープ外の課題が見つかることがよくある。「一緒にやっちゃいたい」こともあれば、本当に後回しでいいこともある。
これを暗黙的に流してしまうと見落とすので、**AskUserQuestion ツールで明示的に確認**する。
「このセッションで対応するか、ログに残して次回に回すか」をユーザーに選ばせる。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; color: #374151; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">小出し出力（separator.py）</h3>
<div style="padding: 12px 20px 16px;">

議題間に**Pythonで空文字を出力するだけのスクリプト**を挟む。
ツール呼び出しが入ることでテキストバッファがフラッシュされ、議題ごとにブロック単位でストリーミング表示される。

</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<h3 style="margin: 0; padding: 12px 20px; font-size: 16px; font-weight: 700; color: #374151; border-bottom: 1px solid #bfdbfe; background: #dbeafe; color: #1d4ed8;">タブ名の自動設定</h3>
<div style="padding: 12px 20px 16px;">

tmux または VS Code のターミナル環境では、議題が決まったタイミング（Phase 2）で tab-rename スキルが発動し、タブにテーマ名が自動で付く。
複数セッションを並列で走らせているときに、どのタブでどんな話をしていたかがパッと見で分かるようになる。

付けられたタブ名は、セッション終了時に save-chatlog → tab-reset の流れでデフォルトに戻る。

</div>
</div>

</div>
