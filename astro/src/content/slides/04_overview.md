# スキル全体像: 2層構成

<p style="padding-inline: 56px; color: #64748b; font-size: 14px; margin: -8px 0 8px;">元々はバラバラだったが、使っているうちに連携させるようになり、基本的にセットで使うようになった。簡易的なものだと summon-experts は使わないこともある。</p>

## 第1層: メインスキル（直列で利用）

<div style="padding: 0 56px; margin-bottom: 8px;">
<div style="display: flex; flex-direction: column;">

<div style="display: flex; gap: 16px; align-items: flex-start;">
<div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0;">
<div style="width: 32px; height: 32px; border-radius: 50%; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">1</div>
<div style="width: 2px; background: #cbd5e1; flex: 1; min-height: 20px; margin-top: 4px;"></div>
</div>
<div style="padding-bottom: 16px; padding-top: 4px;">
<div style="font-weight: 700; font-size: 16px; color: #1e293b;">summon-experts</div>
<div style="font-size: 13px; color: #64748b; margin-top: 2px;">課題を複数ロールで多角的に分析</div>
</div>
</div>

<div style="display: flex; gap: 16px; align-items: flex-start;">
<div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0;">
<div style="width: 32px; height: 32px; border-radius: 50%; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">2</div>
<div style="width: 2px; background: #cbd5e1; flex: 1; min-height: 20px; margin-top: 4px;"></div>
</div>
<div style="padding-bottom: 16px; padding-top: 4px;">
<div style="font-weight: 700; font-size: 16px; color: #1e293b;">planmode-rules</div>
<div style="font-size: 13px; color: #64748b; margin-top: 2px;">プランを組んで検証・改良のサイクル</div>
</div>
</div>

<div style="display: flex; gap: 16px; align-items: flex-start;">
<div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0;">
<div style="width: 32px; height: 32px; border-radius: 50%; background: #94a3b8; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">3</div>
<div style="width: 2px; background: #cbd5e1; flex: 1; min-height: 20px; margin-top: 4px;"></div>
</div>
<div style="padding-bottom: 16px; padding-top: 4px;">
<div style="font-weight: 700; font-size: 16px; color: #94a3b8;">新セッションで実装</div>
</div>
</div>

<div style="display: flex; gap: 16px; align-items: flex-start;">
<div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0;">
<div style="width: 32px; height: 32px; border-radius: 50%; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px;">4</div>
</div>
<div style="padding-top: 4px;">
<div style="font-weight: 700; font-size: 16px; color: #1e293b;">save-chatlog</div>
<div style="font-size: 13px; color: #64748b; margin-top: 2px;">作業ログを保存＆セッションの後処理</div>
</div>
</div>

</div>
</div>

## 第2層: サブツール群

<p style="padding-inline: 56px; font-size: 13px; color: #64748b; margin: -8px 0 12px;">メインスキルを作っているときに「あったら便利」と追加されたもの。複数のスキルから汎用的に使えたり、ユーザーが単独で呼び出すこともある。</p>

<div style="padding: 0 56px; display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 14px;">

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<div style="background: #2563eb; color: white; padding: 8px 14px; font-weight: 700; font-size: 13px; text-align: center;">summon-experts</div>
<div style="padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; background: #f8fafc;">
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">tab-rename</span>
</div>
</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<div style="background: #2563eb; color: white; padding: 8px 14px; font-weight: 700; font-size: 13px; text-align: center;">planmode-rules</div>
<div style="padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; background: #f8fafc;">
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">context-handover</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">current-session-id</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">git-commit-rules</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">skill-design-guide</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat related-tool-cat--agent">エージェント</span>
<span style="font-size: 13px;">impl-checker</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat related-tool-cat--hook">フック</span>
<span style="font-size: 13px;">precompact-handover</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat related-tool-cat--hook">フック</span>
<span style="font-size: 13px;">sessionstart-load-handover</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat related-tool-cat--hook">フック</span>
<span style="font-size: 13px;">send-continue</span>
</div>
</div>
</div>

<div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
<div style="background: #2563eb; color: white; padding: 8px 14px; font-weight: 700; font-size: 13px; text-align: center;">save-chatlog</div>
<div style="padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; background: #f8fafc;">
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">current-session-id</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">git-commit-rules</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span class="related-tool-cat">スキル</span>
<span style="font-size: 13px;">tab-reset</span>
</div>
</div>
</div>

</div>
