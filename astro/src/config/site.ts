/**
 * サイト設定（ウェビナー用スライドサイト）
 */

// ==========================================
// サイト基本情報
// ==========================================
export const SITE = {
  name: "Claude Code グローバルスキル構成の紹介",
  url: "https://example.com",
  locale: "ja_JP",
} as const;

// ==========================================
// SEO設定
// ==========================================
export const SEO = {
  title: "Claude Code グローバルスキル構成の紹介",
  description: "ウェビナー用スライド: summon-experts / planmode-rules / save-chatlog の3スキルと関連サブツールの紹介",
  keywords: [
    "Claude Code",
    "スキル",
    "ウェビナー",
  ],
  ogImage: "/images/ogp.webp",
} as const;
