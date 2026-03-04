"""Tab Rename セットアップスクリプト

VS Code 拡張機能のシンボリックリンクを ~/.vscode/extensions/ に作成する。
スキル実行時に自動的に呼び出され、リンクが未作成なら作成する。
"""

import json
import sys
from pathlib import Path


def _cleanup_old_extension_registry(extensions_dir: Path) -> None:
    """extensions.json から旧拡張機能 satokupo.terminal-renamer のエントリを削除する。"""
    registry = extensions_dir / "extensions.json"
    if not registry.is_file():
        return

    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"警告: extensions.json の読み込みに失敗しました: {e}", file=sys.stderr)
        return

    if not isinstance(data, list):
        return

    filtered = [
        entry for entry in data
        if not (
            isinstance(entry, dict)
            and isinstance(entry.get("identifier"), dict)
            and entry["identifier"].get("id") == "satokupo.terminal-renamer"
        )
    ]

    if len(filtered) == len(data):
        return

    try:
        registry.write_text(
            json.dumps(filtered, indent="\t", ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"extensions.json から旧エントリ satokupo.terminal-renamer を削除しました")
    except OSError as e:
        print(f"警告: extensions.json の書き込みに失敗しました: {e}", file=sys.stderr)


def main():
    # スキルディレクトリはシンボリックリンク経由のため .resolve() でリンク解決
    extension_src = Path(__file__).resolve().parent.parent / "vscode-extension"

    if not extension_src.is_dir():
        print(
            f"エラー: 拡張機能ソースが見つかりません: {extension_src}",
            file=sys.stderr,
        )
        sys.exit(1)

    extensions_dir = Path.home() / ".vscode" / "extensions"
    extensions_dir.mkdir(parents=True, exist_ok=True)

    # 旧リンク（terminal-renamer）が残っていれば削除
    old_link = extensions_dir / "terminal-renamer"
    if old_link.is_symlink():
        old_link.unlink()
        print(f"旧リンクを削除しました: {old_link}")

    # extensions.json から旧エントリを削除
    _cleanup_old_extension_registry(extensions_dir)

    link_path = extensions_dir / "tab-renamer"

    # 既にリンクが存在し、リンク先が正しい場合はスキップ
    if link_path.is_symlink():
        current_target = link_path.resolve()
        if current_target == extension_src.resolve():
            print(f"セットアップ済み: {link_path} -> {extension_src}")
            return
        # リンク先が異なる場合は再作成
        print(f"リンク先を更新: {link_path}")
        link_path.unlink()
    elif link_path.exists():
        print(
            f"エラー: {link_path} が既に存在します（シンボリックリンクではありません）",
            file=sys.stderr,
        )
        print("手動で削除してから再実行してください", file=sys.stderr)
        sys.exit(1)

    link_path.symlink_to(extension_src)
    print(f"シンボリックリンクを作成しました: {link_path} -> {extension_src}")
    print("VS Code のリロード（Developer: Reload Window）が必要です")


if __name__ == "__main__":
    main()
