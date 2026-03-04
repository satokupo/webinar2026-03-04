"""tmux環境の検出と後片付けフローへの誘導."""

import os


def main():
    if os.environ.get("TMUX"):
        print(
            "🔧 tmux環境を検出しました。後片付けフローに進みます。"
            "SKILL.md の「後片付け（tmux環境のみ）」セクションに従い、"
            "AskUserQuestion でユーザーに次のアクションを確認してください。"
        )
    else:
        print("✅ すべての作業が完了しました。")


if __name__ == "__main__":
    main()
