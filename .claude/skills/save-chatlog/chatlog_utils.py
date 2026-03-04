#!/usr/bin/env python3
"""
チャットログ保存スキル用ユーティリティ

使用方法:
    python3 chatlog_utils.py mkdir <path>
    python3 chatlog_utils.py write <path> <content>
    python3 chatlog_utils.py gitignore <path> <entry>
    python3 chatlog_utils.py find-jsonl <cwd>
    python3 chatlog_utils.py list-sessions <cwd>
    python3 chatlog_utils.py save <output_path> --cwd <cwd> --title "..." --tags "..." --summary "..."
                                              -g "検索文字列" [--merge-id <session_id>]
                                              [--offset N] [--merge-until N] [--auto-merge]
                                              [--commits "hash1,hash2"]

セッション特定オプション:
    --session-id ID     セッションIDを直接指定（推奨・並列稼働対応）
    -g, --grep          ユーザーの日本語発言でセッションを特定
    --offset N          N個前のセッションを指定（0=最新、並列稼働時は使用注意）

マージオプション:
    --auto-merge        プランファイルから planning-session を自動検出してマージ（推奨）
    --merge-id ID       指定したセッションIDと現在のセッションをマージ
    -m, --merge-until N offset〜Nまでの範囲をマージ（並列稼働時は使用注意）
"""

import argparse
import os
import re
import sys
from datetime import datetime
from typing import Optional

from session_finder import (
    find_jsonl_path,
    find_jsonl_path_by_grep,
    find_jsonl_path_by_session_id,
    find_jsonl_paths_range,
    get_all_jsonl_files,
    get_saved_session_ids,
    parse_jsonl,
)
from plan_manager import (
    archive_plan_files,
    cleanup_planmode_temp_files,
    convert_to_relative_plan_paths,
    extract_planning_session,
    sanitize_title,
)


def mkdir(path: str) -> None:
    """ディレクトリを作成する（親ディレクトリも含めて）"""
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")


def write(path: str, content: str) -> None:
    """ファイルを作成する"""
    # 親ディレクトリがなければ作成
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Written: {path}")


def gitignore(path: str, entry: str) -> None:
    """
    .gitignore にエントリを追加する
    path: .gitignore のパス
    entry: 追加するエントリ（例: '_chatlog/'）
    """
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if entry in content:
            print(f"Already exists in {path}: {entry}")
            return
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f'\n# チャットログ（Git管理外）\n{entry}\n')
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'# チャットログ（Git管理外）\n{entry}\n')
    print(f"Added to {path}: {entry}")


def find_jsonl(offset: int = 0) -> None:
    """JSONLファイルを特定して出力（コマンド用）"""
    try:
        jsonl_path = find_jsonl_path(offset)
        print(jsonl_path)
    except (FileNotFoundError, IndexError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def list_sessions(cwd: str) -> None:
    """
    利用可能なセッション一覧を表示
    """
    try:
        files_with_mtime = get_all_jsonl_files()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    saved_ids = get_saved_session_ids(cwd)

    print(f"{'Offset':<6} {'Session ID':<38} {'Updated':<20} {'Status'}")
    print('-' * 80)

    for idx, (path, mtime) in enumerate(files_with_mtime):
        session_id = os.path.basename(path).replace('.jsonl', '')
        updated = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        status = '保存済み' if session_id in saved_ids else '未保存'
        print(f"{idx:<6} {session_id:<38} {updated:<20} {status}")


def save(output_path: str, cwd: str, title: str, tags: str, summary: str,
         offset: int = 0, merge_until: Optional[int] = None,
         grep: Optional[str] = None, merge_session_id: Optional[str] = None,
         auto_merge: bool = False, session_id: Optional[str] = None,
         commits: Optional[str] = None) -> None:
    """
    チャットログをマークダウンで保存

    Args:
        output_path: 出力ファイルパス
        cwd: 作業ディレクトリ
        title: タイトル
        tags: タグ（カンマ区切り）
        summary: 要約
        offset: 0=最新, N=N個前
        merge_until: 指定時、offset ~ merge_until をマージ
        grep: 指定時、この文字列を含むセッションを特定
        merge_session_id: 指定時、このセッションIDと現在のセッションをマージ
        auto_merge: プランファイルから planning-session を自動検出してマージ
        session_id: 現在のセッションIDを直接指定（推奨）
        commits: コミットハッシュ（カンマ区切り文字列、例: "abc1234,def5678"）
    """
    plan_files = []

    # 現在のセッションを特定
    current_path = None
    if session_id:
        current_path = find_jsonl_path_by_session_id(session_id)
    elif grep:
        current_path = find_jsonl_path_by_grep(grep)

    # auto_merge モードの場合、planning-session を自動検出
    if auto_merge and current_path and merge_session_id is None:
        parsed = parse_jsonl(current_path)

        planning_session_id = None

        # 方法1: plan_files から検出（プランを作成したセッション）
        for pf in parsed.get('plan_files', []):
            ps_id = extract_planning_session(pf)
            if ps_id and ps_id != parsed['session_id']:
                planning_session_id = ps_id
                break

        # 方法2: 会話内容から直接検出（プランを読み込んで実装したセッション）
        if planning_session_id is None:
            for role, content in parsed.get('conversations', []):
                match = re.search(r'planning-session:\s*([a-f0-9-]{36})', content)
                if match:
                    ps_id = match.group(1)
                    if ps_id != parsed['session_id']:
                        planning_session_id = ps_id
                        break

        if planning_session_id:
            merge_session_id = planning_session_id
            print(f"Auto-detected planning-session: {planning_session_id}", file=sys.stderr)

    if merge_session_id is not None:
        # セッションID指定でのマージモード（推奨）
        # merge_session_id が古い方（計画）、current_path で特定した現在のセッションが新しい方（実装）
        if not current_path:
            raise ValueError("--merge-id を使用する場合は --session-id または -g も必須です")
        # マージ対象セッション（ID指定）
        merge_path = find_jsonl_path_by_session_id(merge_session_id)

        # merge-idが古い（計画）、currentが新しい（実装）の順で結合
        jsonl_paths = [merge_path, current_path]  # 古い順

        all_conversations = []
        session_ids = []
        all_plan_files = []
        earliest_start_time = None

        for jsonl_path in jsonl_paths:
            parsed = parse_jsonl(jsonl_path)
            session_ids.append(parsed['session_id'])
            all_conversations.extend(parsed['conversations'])
            all_plan_files.extend(parsed.get('plan_files', []))
            if earliest_start_time is None or parsed['start_time'] < earliest_start_time:
                earliest_start_time = parsed['start_time']

        start_time = earliest_start_time
        conversations = all_conversations
        plan_files = list(set(all_plan_files))  # 重複除去

        # マージ用フロントマター（session_ids: 配列形式）
        session_ids_yaml = '\n'.join(f'  - {sid}' for sid in session_ids)
        session_block = f"session_ids:\n{session_ids_yaml}"

    elif merge_until is not None:
        # offset範囲指定でのマージモード（従来方式、並列稼働時は使用注意）
        print("Warning: --merge-until は並列稼働時に正確なセッション特定ができない場合があります。",
              file=sys.stderr)
        print("推奨: --merge-id <session_id> を使用してください。", file=sys.stderr)

        jsonl_paths = find_jsonl_paths_range(offset, merge_until)
        all_conversations = []
        session_ids = []
        all_plan_files = []
        earliest_start_time = None

        for jsonl_path in jsonl_paths:
            parsed = parse_jsonl(jsonl_path)
            session_ids.append(parsed['session_id'])
            all_conversations.extend(parsed['conversations'])
            all_plan_files.extend(parsed.get('plan_files', []))
            if earliest_start_time is None or parsed['start_time'] < earliest_start_time:
                earliest_start_time = parsed['start_time']

        start_time = earliest_start_time
        conversations = all_conversations
        plan_files = list(set(all_plan_files))  # 重複除去

        # マージ用フロントマター（session_ids: 配列形式）
        session_ids_yaml = '\n'.join(f'  - {sid}' for sid in session_ids)
        session_block = f"session_ids:\n{session_ids_yaml}"
    else:
        # 単一セッションモード
        if current_path:
            # session_id または grep で特定済み
            jsonl_path = current_path
        else:
            # 従来通りoffsetで特定
            jsonl_path = find_jsonl_path(offset)
        parsed = parse_jsonl(jsonl_path)
        start_time = parsed['start_time']
        conversations = parsed['conversations']
        plan_files = parsed.get('plan_files', [])
        session_block = f"session_id: {parsed['session_id']}"

    # output_path の解決（collect_errors に chatlog_path を渡すため、先に実行する）
    if output_path.endswith('/'):
        timestamp = start_time.strftime('%Y%m%d-%H%M%S')
        year = start_time.strftime('%Y')
        month = start_time.strftime('%m')
        safe_title = sanitize_title(title)
        filename = f"{timestamp}_{safe_title}.md"
        output_path = os.path.join(output_path, year, month, filename)

    # エラー収集
    from error_collector import collect_errors
    session_id_value = session_ids[-1] if (merge_session_id is not None or merge_until is not None) else parsed['session_id']
    collect_errors(conversations, session_id_value, start_time, cwd, chatlog_path=output_path)

    # planmode 一時ファイルのクリーンアップ用 ID を収集
    # archive_plan_files() の前に実行する（アーカイブ後はファイルパスが変わるため）
    #
    # save() 関数はマージモード（複数セッション統合）と単一セッションモードの
    # 2つの経路を持つ。クリーンアップ対象のIDは経路によって異なる:
    # - マージモード: session_ids（統合対象の全セッションID）
    # - 単一モード: parsed['session_id']（現在のセッションのみ）
    # いずれの場合も、プランファイルの planning-session ID を追加する
    if merge_session_id is not None or merge_until is not None:
        planmode_cleanup_ids = list(session_ids)
    else:
        planmode_cleanup_ids = [parsed['session_id']]
    for pf in plan_files:
        ps_id = extract_planning_session(pf)
        if ps_id and ps_id not in planmode_cleanup_ids:
            planmode_cleanup_ids.append(ps_id)

    # プランファイルをアーカイブ（タイムスタンプ付きパスに移動）
    plan_files = archive_plan_files(plan_files, cwd)

    # planmode 一時ファイルをクリーンアップ
    cleanup_planmode_temp_files(cwd, planmode_cleanup_ids)

    # プランファイルパスを相対パスに変換
    relative_plan_files = convert_to_relative_plan_paths(plan_files, cwd)

    # プランファイル用フロントマターブロック生成
    if len(relative_plan_files) == 1:
        plan_block = f"plan_file: {relative_plan_files[0]}"
    elif len(relative_plan_files) > 1:
        plan_yaml = '\n'.join(f'  - {p}' for p in relative_plan_files)
        plan_block = f"plan_files:\n{plan_yaml}"
    else:
        plan_block = ""

    # コミットハッシュ用フロントマターブロック生成
    if commits:
        commits_list = [c.strip() for c in commits.split(',') if c.strip()]
    else:
        commits_list = []
    if commits_list:
        commits_yaml = '\n'.join(f'  - {c}' for c in commits_list)
        commits_block = f"commits:\n{commits_yaml}"
    else:
        commits_block = ""

    # フロントマター生成
    date_str = start_time.strftime('%Y-%m-%d')
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    tags_yaml = '\n'.join(f'  - {t}' for t in tags_list)

    # オプショナルブロックを結合（plan_block, commits_block）
    optional_blocks = '\n'.join(b for b in [plan_block, commits_block] if b)
    if optional_blocks:
        frontmatter = f"""---
date: {date_str}
{session_block}
{optional_blocks}
title: {title}
tags:
{tags_yaml}
summary: |
  {summary}
---"""
    else:
        frontmatter = f"""---
date: {date_str}
{session_block}
title: {title}
tags:
{tags_yaml}
summary: |
  {summary}
---"""

    # マークダウン本文を生成
    content_parts = [frontmatter, '', f'# {title}', '']
    for role, text in conversations:
        content_parts.append(f'## {role}')
        content_parts.append('')
        content_parts.append(text)
        content_parts.append('')

    markdown_content = '\n'.join(content_parts)

    # 親ディレクトリがなければ作成
    parent = os.path.dirname(output_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    # ファイル保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'mkdir':
        if len(sys.argv) < 3:
            print("Usage: python3 chatlog_utils.py mkdir <path>")
            sys.exit(1)
        mkdir(sys.argv[2])

    elif command == 'write':
        if len(sys.argv) < 4:
            print("Usage: python3 chatlog_utils.py write <path> <content>")
            sys.exit(1)
        write(sys.argv[2], sys.argv[3])

    elif command == 'gitignore':
        if len(sys.argv) < 4:
            print("Usage: python3 chatlog_utils.py gitignore <path> <entry>")
            sys.exit(1)
        gitignore(sys.argv[2], sys.argv[3])

    elif command == 'find-jsonl':
        offset = 0
        # 従来の位置引数 cwd は無視（後方互換）
        args = sys.argv[2:]
        for i, arg in enumerate(args):
            if arg == '--offset' and i + 1 < len(args):
                offset = int(args[i + 1])
        find_jsonl(offset)

    elif command == 'list-sessions':
        if len(sys.argv) < 3:
            print("Usage: python3 chatlog_utils.py list-sessions <cwd>")
            sys.exit(1)
        list_sessions(sys.argv[2])

    elif command == 'save':
        # argparseでオプション引数を処理
        parser = argparse.ArgumentParser(prog='chatlog_utils.py save')
        parser.add_argument('output_path', help='出力ベースディレクトリ（例: _chatlog/）。末尾 / でファイル名自動生成')
        parser.add_argument('--cwd', required=True, help='作業ディレクトリ（JSONLを自動特定）')
        parser.add_argument('--title', required=True, help='タイトル')
        parser.add_argument('--tags', required=True, help='タグ（カンマ区切り）')
        parser.add_argument('--summary', required=True, help='要約')
        parser.add_argument('--offset', type=int, default=0,
                            help='セッションオフセット（0=最新, 1=1個前, ...）')
        parser.add_argument('-m', '--merge-until', type=int, default=None,
                            help='マージ終了オフセット（指定時、offset〜merge-untilをマージ、並列稼働時は使用注意）')
        parser.add_argument('--session-id', type=str, default=None,
                            help='現在のセッションIDを直接指定（推奨・並列稼働対応）')
        parser.add_argument('-g', '--grep', type=str, default=None,
                            help='この文字列を含むセッションを特定')
        parser.add_argument('--merge-id', type=str, default=None,
                            help='マージ対象のセッションID（プランファイルに記録されたIDを指定）')
        parser.add_argument('--auto-merge', action='store_true', default=False,
                            help='プランファイルから planning-session を自動検出してマージ')
        parser.add_argument('--commits', type=str, default=None,
                            help='コミットハッシュ（カンマ区切り）')
        args = parser.parse_args(sys.argv[2:])
        save(args.output_path, args.cwd, args.title, args.tags, args.summary,
             args.offset, args.merge_until, args.grep, args.merge_id, args.auto_merge,
             args.session_id, commits=args.commits)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
