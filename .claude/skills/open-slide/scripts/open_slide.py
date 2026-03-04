import sys
import webbrowser
from pathlib import Path

# __file__: scripts/open_slide.py
# parents[0] = scripts/
# parents[1] = open-slide/
# parents[2] = skills/
# parents[3] = .claude/
# parents[4] = project root
project_root = Path(__file__).resolve().parents[4]
slide_path = project_root / "astro" / "dist" / "index.html"

if not slide_path.exists():
    print(f"Error: スライドが見つかりません: {slide_path}", file=sys.stderr)
    sys.exit(1)

file_uri = slide_path.as_uri()
webbrowser.open(file_uri)
print(f"ブラウザでスライドを開きました: {file_uri}")
