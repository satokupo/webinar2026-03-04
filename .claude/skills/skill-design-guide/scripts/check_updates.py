#!/usr/bin/env python3
"""skill-design-guide 自動更新チェック用スクリプト"""
import subprocess
import sys
import json


def _fetch_releases() -> list:
    """GitHub Releases API からリリース一覧を取得"""
    cmd = ["gh", "api", "repos/anthropics/claude-code/releases"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def _filter_skill_releases(releases: list, last_checked_date: str) -> list:
    """前回チェック日以降のスキル関連リリースをフィルタ"""
    filtered = []
    for release in releases:
        if release["published_at"] > last_checked_date:
            if "skill" in (release.get("body") or "").lower():
                filtered.append({
                    "version": release["tag_name"],
                    "date": release["published_at"],
                    "body": release["body"],
                })
    return filtered


def check_release_count(last_checked_date: str) -> int:
    """前回チェック日以降のスキル関連リリース件数を返す"""
    releases = _fetch_releases()
    return len(_filter_skill_releases(releases, last_checked_date))


def get_release_details(last_checked_date: str) -> str:
    """前回チェック日以降のスキル関連リリースの詳細をJSON形式で返す"""
    releases = _fetch_releases()
    filtered = _filter_skill_releases(releases, last_checked_date)
    return json.dumps(filtered, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: check_updates.py <last_checked_date> [--details]",
            file=sys.stderr,
        )
        sys.exit(1)

    date = sys.argv[1]
    if "--details" in sys.argv:
        print(get_release_details(date))
    else:
        print(check_release_count(date))
