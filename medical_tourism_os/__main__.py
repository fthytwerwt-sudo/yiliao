"""
用途：
提供 `python3 -m medical_tourism_os` 的统一 CLI 入口。

上游：
本地开发者、测试和未来脚本通过模块运行方式调用这里。

下游：
把参数转发给 `interfaces.cli.run_cli`，输出离线安全 JSON。

边界：
这里不持有业务状态；具体命令仍停留在 synthetic / dry-run 范围。
"""

from __future__ import annotations

import sys
from typing import Optional, Sequence

from medical_tourism_os.interfaces.cli import run_cli


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    作用：
    把命令参数转发给统一 CLI。

    关键边界：
    入口层不自行解释业务命令，避免与 `interfaces.cli` 分叉。
    """

    command_argv = list(argv) if argv is not None else sys.argv[1:]
    return run_cli(command_argv, output=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
