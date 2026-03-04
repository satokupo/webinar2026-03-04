/**
 * postbuild.mjs
 * astro build 後に dist/ 内の全HTMLの絶対パスを相対パスに変換する。
 * file:// で直接開いても CSS・リンクが機能するようにする。
 */

import { readdir, readFile, writeFile } from 'fs/promises';
import { join, relative, dirname, extname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = join(__dirname, 'dist');

async function findHtmlFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await findHtmlFiles(fullPath));
    } else if (entry.name.endsWith('.html')) {
      files.push(fullPath);
    }
  }
  return files;
}

/**
 * ファイルの dist/ からの深さに応じた相対プレフィックスを返す
 * dist/index.html        → "."
 * dist/foo/index.html    → ".."
 * dist/foo/bar/index.html → "../.."
 */
function getPrefix(filePath) {
  const rel = relative(distDir, dirname(filePath));
  if (!rel) return '.';
  const depth = rel.split('/').length;
  return Array(depth).fill('..').join('/');
}

/**
 * HTML内の href/src の絶対パスを相対パスに変換する
 * /          → {prefix}/
 * /foo       → {prefix}/foo/   (拡張子なし = ページディレクトリ)
 * /_astro/x.css → {prefix}/_astro/x.css (拡張子あり = ファイル)
 */
function convertAbsolutePaths(html, prefix) {
  // href/src 属性の変換
  let result = html.replace(/(href|src)="(\/[^"]*?)"/g, (match, attr, path) => {
    if (path === '/') {
      return `${attr}="${prefix}/index.html"`;
    }
    const trimmed = path.slice(1); // 先頭の / を除去
    const ext = extname(trimmed);
    if (ext) {
      return `${attr}="${prefix}/${trimmed}"`;
    } else {
      return `${attr}="${prefix}/${trimmed}/index.html"`;
    }
  });

  // JS変数（prevSlug/nextSlug）の絶対パスを変換
  result = result.replace(/(prevSlug|nextSlug)\s*=\s*"(\/[^"]*?)"/g, (match, varName, path) => {
    if (path === '/') {
      return `${varName} = "${prefix}/index.html"`;
    }
    const trimmed = path.slice(1);
    return `${varName} = "${prefix}/${trimmed}/index.html"`;
  });

  return result;
}

const htmlFiles = await findHtmlFiles(distDir);
let count = 0;

for (const file of htmlFiles) {
  const html = await readFile(file, 'utf-8');
  const prefix = getPrefix(file);
  const converted = convertAbsolutePaths(html, prefix);
  if (html !== converted) {
    await writeFile(file, converted, 'utf-8');
    count++;
  }
}

console.log(`✅ ${count}/${htmlFiles.length} ファイルを相対パスに変換しました`);
