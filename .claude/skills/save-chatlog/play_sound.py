#!/usr/bin/env python3
import subprocess
import os
import sys


def main():
    sound_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound")
    sound_file = os.path.join(sound_dir, "テッテレー.mp3")

    if not os.path.exists(sound_file):
        print(f"音源ファイルが見つかりません: {sound_file}", file=sys.stderr)
        sys.exit(1)

    subprocess.run(["afplay", sound_file], check=True)


if __name__ == "__main__":
    main()
