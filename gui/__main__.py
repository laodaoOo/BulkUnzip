"""支持 `python -m gui` 启动。"""

from __future__ import annotations

from gui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
