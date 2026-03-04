"""プランファイル管理モジュール

プランファイルの解析・アーカイブ・planmode一時ファイルのクリーンアップを担当する。
"""

import os
import re
import shutil
import sys
from datetime import datetime
from typing import List, Optional


def extract_planning_session(plan_file_path: str) -> Optional[str]:
    """プランファイルのフロントマターから planning-session を抽出する。

    Args:
        plan_file_path: プランファイルの絶対パス

    Returns:
        planning-session の値（UUID）、なければ None
    """
    if not os.path.exists(plan_file_path):
        return None

    try:
        with open(plan_file_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # フロントマターは先頭にあるので1000文字で十分

        # フロントマター内の planning-session を探す
        match = re.search(r'^planning-session:\s*([a-f0-9-]{36})', content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def extract_plan_title(plan_path: str) -> str:
    """プランファイルの H1 見出しからタイトルを取得する。

    Args:
        plan_path: プランファイルの絶対パス

    Returns:
        タイトル文字列。見つからなければファイル名（拡張子なし）
    """
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
    except Exception:
        pass
    return os.path.splitext(os.path.basename(plan_path))[0]


def sanitize_title(title: str) -> str:
    """ファイル名に使えない文字を _ に置換する。"""
    return re.sub(r'[/:\\]', '_', title)


def cleanup_planmode_temp_files(cwd: str, session_ids: List[str]) -> None:
    """planmode-rules が生成した一時ファイルを削除する。

    .claude/temp/ 内のセッションIDプレフィックス付きファイル（{sid}_*.md）を
    一括削除する。conversation, handover, codex-review 等すべてが対象。

    Args:
        cwd: プロジェクトルート
        session_ids: 削除対象のセッションIDリスト
    """
    temp_dir = os.path.join(cwd, ".claude", "temp")
    if not os.path.isdir(temp_dir):
        return

    for sid in session_ids:
        for filename in os.listdir(temp_dir):
            if filename.startswith(f"{sid}_"):
                filepath = os.path.join(temp_dir, filename)
                os.remove(filepath)
                print(f"Cleaned planmode temp: {filepath}", file=sys.stderr)


def archive_plan_files(plan_files: List[str], cwd: str = "") -> List[str]:
    """プランファイルをアーカイブする。誤配置検知・agent ファイル削除・退避も行う。

    Args:
        plan_files: プランファイルの絶対パスリスト
        cwd: プロジェクトルート（誤配置検知に使用）

    Returns:
        アーカイブ後のパスリスト（移動しなかったものは元パスのまま）
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    year = now.strftime("%Y")
    month = now.strftime("%m")

    correct_plans_dir = os.path.join(cwd, ".claude", "plans") if cwd else ""
    misplaced_dirs = set()  # 退避対象の誤配置 .claude/ ディレクトリ

    # --- Phase A: agent ファイルの自動検出 ---
    agent_cleanup = []
    for plan_path in list(plan_files):
        if not os.path.exists(plan_path):
            continue
        basename = os.path.basename(plan_path)
        if "-agent-" in basename:
            continue  # agent ファイル自身はスキップ
        stem = os.path.splitext(basename)[0]
        plan_dir = os.path.dirname(plan_path)
        for f in os.listdir(plan_dir):
            if f.startswith(stem + "-agent-") and f.endswith(".md"):
                agent_path = os.path.join(plan_dir, f)
                if agent_path not in plan_files:
                    agent_cleanup.append(agent_path)

    # --- Phase B: メインプランのアーカイブ ---
    archived = []
    for plan_path in plan_files:
        if not os.path.exists(plan_path):
            continue

        # すでに年月ディレクトリ内にある場合はスキップ
        if re.search(r'/\d{4}/\d{2}/', plan_path):
            archived.append(plan_path)
            continue

        # パス検証: プロジェクトルートの .claude/plans/ 配下か
        is_misplaced = False
        if correct_plans_dir and not plan_path.startswith(correct_plans_dir + "/"):
            is_misplaced = True
            print(f"WARNING: Plan file misplaced: {plan_path}", file=sys.stderr)
            print(f"  Expected under: {correct_plans_dir}/", file=sys.stderr)

            # 誤配置の .claude/ ディレクトリを記録
            claude_idx = plan_path.find("/.claude/")
            if claude_idx != -1:
                misplaced_claude_dir = plan_path[:claude_idx + len("/.claude")]
                root_claude = os.path.join(cwd, ".claude")
                if os.path.abspath(misplaced_claude_dir) != os.path.abspath(root_claude):
                    misplaced_dirs.add(misplaced_claude_dir)

            base_dir = correct_plans_dir  # 正しい場所にアーカイブ
        else:
            base_dir = os.path.dirname(plan_path)

        target_dir = os.path.join(base_dir, year, month)
        os.makedirs(target_dir, exist_ok=True)

        title = extract_plan_title(plan_path)
        safe_title = sanitize_title(title)
        new_filename = f"{timestamp}_{safe_title}.md"
        new_path = os.path.join(target_dir, new_filename)

        # 誤配置の場合は shutil.move（クロスディレクトリ移動に対応）
        if is_misplaced:
            shutil.move(plan_path, new_path)
        else:
            os.rename(plan_path, new_path)
        print(f"Archived: {plan_path} -> {new_path}", file=sys.stderr)
        archived.append(new_path)

    # --- Phase C: agent ファイルの削除（一時ファイルと同じ扱い） ---
    for agent_path in agent_cleanup:
        if os.path.exists(agent_path):
            os.remove(agent_path)
            print(f"Removed agent file: {agent_path}", file=sys.stderr)

    # --- Phase D: 誤配置 .claude/ を .claude/temp/ に退避 ---
    # グローバル ~/.claude はプランファイルの移動のみ行い、ディレクトリ退避はしない
    global_claude = os.path.expanduser("~/.claude")
    for misplaced_dir in misplaced_dirs:
        if os.path.abspath(misplaced_dir) == os.path.abspath(global_claude):
            print(f"Skipped evacuation of global .claude/: {misplaced_dir}",
                  file=sys.stderr)
            continue
        if os.path.isdir(misplaced_dir):
            parent_name = os.path.basename(os.path.dirname(misplaced_dir))
            evacuate_name = f"misplaced_{parent_name}_{timestamp}"
            evacuate_dir = os.path.join(cwd, ".claude", "temp", evacuate_name)
            os.makedirs(os.path.dirname(evacuate_dir), exist_ok=True)
            shutil.move(misplaced_dir, evacuate_dir)
            print(f"Evacuated misplaced .claude/: {misplaced_dir} -> {evacuate_dir}",
                  file=sys.stderr)

    return archived


def convert_to_relative_plan_paths(plan_files: List[str], cwd: str) -> List[str]:
    """プランファイルの絶対パスをプロジェクトルートからの相対パスに変換する。

    Args:
        plan_files: プランファイルの絶対パスリスト
        cwd: 作業ディレクトリ（プロジェクトルート）

    Returns:
        相対パスのリスト
    """
    relative_paths = []
    cwd_normalized = cwd.rstrip('/')

    for pf in plan_files:
        if pf.startswith(cwd_normalized):
            # プロジェクトルート配下のパス
            relative_paths.append(pf[len(cwd_normalized):].lstrip('/'))
        elif '/.claude/plans/' in pf:
            # プロジェクトルート外の場合は .claude/plans/ 以降を使用
            idx = pf.find('/.claude/plans/')
            relative_paths.append(pf[idx + 1:])
        else:
            # フォールバック: そのまま追加
            relative_paths.append(pf)

    return relative_paths
