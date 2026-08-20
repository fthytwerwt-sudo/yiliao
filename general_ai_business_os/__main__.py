"""提供 `python -m general_ai_business_os` 的安全 CLI 入口。"""

from __future__ import annotations

import sys

from general_ai_business_os.interfaces.cli import run_cli


if __name__ == "__main__":
    sys.exit(run_cli())
