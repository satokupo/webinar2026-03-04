/**
 * HTML文字列内のサブツール名を <button data-popup="name"> に変換する
 * 名前が長い順にソートして部分一致を防止
 */
export function injectPopupLinks(html: string, popupNames: string[]): string {
  // 長い名前から順に処理（部分一致防止）
  const sorted = [...popupNames].sort((a, b) => b.length - a.length);

  for (const name of sorted) {
    // コードブロック(<code>...</code>)内は変換しない
    // テキストノード相当の箇所のみ置換（タグ属性内・既存button内は対象外）
    // シンプルな方針: タグの外側のテキストのみを対象に置換
    const escaped = name.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
    const regex = new RegExp(`(?<!<[^>]*)\\b(${escaped})\\b(?![^<]*>)`, 'g');
    html = html.replace(regex, (match) => {
      return `<button class="popup-link" data-popup="${name}">${match}</button>`;
    });
  }

  return html;
}
