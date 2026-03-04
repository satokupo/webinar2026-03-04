"""Tab Rename - タブ（tmux window）名を変更するヘルパースクリプト"""

import os
import subprocess
import sys
import urllib.parse


def main():
    args = sys.argv[1:]

    if not args:
        print("エラー: タイトルを引数で指定してください", file=sys.stderr)
        print("使い方: python3 rename_tab.py <タイトル>", file=sys.stderr)
        sys.exit(1)

    title = args[0]

    # 環境判定: tmux → VS Code → 非対応
    tmux_env = os.environ.get("TMUX")
    if tmux_env:
        tmux_pane = os.environ.get("TMUX_PANE", "")
        cmd = ["tmux", "rename-window"]
        if tmux_pane:
            cmd += ["-t", tmux_pane]
        else:
            print("注意: TMUX_PANE未設定のためカレントウィンドウを対象にします", file=sys.stderr)
        cmd.append(title)
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("エラー: tmux rename-window に失敗しました", file=sys.stderr)
            sys.exit(1)
        print(f"タブ名を「{title}」に変更しました")

        # --- tmux セッション名の自動リネーム ---
        # 現在のセッション名を取得
        session_result = subprocess.run(
            ["tmux", "display-message", "-p", "#S"],
            capture_output=True, text=True
        )
        if session_result.returncode == 0:
            session_name = session_result.stdout.strip()
            # デフォルト名（数字のみ）の場合、作業ディレクトリ名に変更
            if session_name.isdigit():
                dirname = os.path.basename(os.getcwd())
                if dirname:  # 空文字でないことを確認
                    rename_result = subprocess.run(
                        ["tmux", "rename-session", dirname]
                    )
                    if rename_result.returncode == 0:
                        print(f"セッション名を「{dirname}」に変更しました（デフォルト名 {session_name} から）")

        return

    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program == "vscode":
        encoded = urllib.parse.quote(title)
        uri = f"vscode://satokupo.tab-renamer/rename?name={encoded}"
        subprocess.run(["open", uri])
        print(f"タブ名を「{title}」に変更しました")

        return

    print(
        f"エラー: 非対応環境です (TMUX未設定, TERM_PROGRAM={term_program!r})",
        file=sys.stderr,
    )
    print("tmux環境またはVS Code統合ターミナルで使用してください", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
