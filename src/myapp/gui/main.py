import sys
from pathlib import Path

# Ensure project `src` is on sys.path when run directly
if __package__ is None:
    p = Path(__file__).resolve()
    src_dir = None
    for parent in p.parents:
        if (parent / "myapp").is_dir():
            src_dir = parent
            break
    if src_dir is None:
        try:
            src_dir = p.parents[2]
        except Exception:
            src_dir = p.parent
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from myapp.gui.windows import run_gui


def run():
    run_gui()


if __name__ == "__main__":
    run()
