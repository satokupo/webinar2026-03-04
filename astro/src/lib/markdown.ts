import fs from 'fs';
import path from 'path';
import { marked } from 'marked';

/**
 * .mdファイルへの相対リンクをリンクなしテキストに変換する
 * 変換後に injectPopupLinks がスキル名をポップアップボタンに変換する
 */
function stripMdLinks(html: string): string {
  return html.replace(/<a href="[^"]*\.md"[^>]*>(.*?)<\/a>/g, '$1');
}

/**
 * astro/src/content/popups/ からカテゴリ付きパスでmdを読み込む
 * 例: loadPopupMarkdown('skills/tab-rename.md')
 */
export async function loadPopupMarkdown(relativePath: string): Promise<string> {
  const fullPath = path.resolve(process.cwd(), 'src/content/popups', relativePath);
  const raw = fs.readFileSync(fullPath, 'utf-8');
  return stripMdLinks(await marked(raw));
}

/**
 * astro/src/content/slides/ からファイル名でmdを読み込み
 * markedでHTMLに変換して返す（スライドページ用）
 */
export async function loadSlideMarkdown(filename: string): Promise<string> {
  const fullPath = path.resolve(process.cwd(), 'src/content/slides', filename);
  const raw = fs.readFileSync(fullPath, 'utf-8');
  return stripMdLinks(await marked(raw));
}
