"""
用途：
提供 `python3 -m medical_tourism_os` 的最小命令行入口。

上游：
本地开发者、测试与后续 CLI 扩展通过模块运行入口调用。

下游：
config 模块输出默认配置快照，供人工确认系统是否仍处于离线安全模式。

边界：
这里只输出本地状态，不初始化数据库、不调用外部服务、不写入业务数据。
"""

from __future__ import annotations

import argparse
import json
from typing import Optional, Sequence

from medical_tourism_os.config import SystemConfig


def build_parser() -> argparse.ArgumentParser:
    """
    作用：
    构建 Phase 1 的最小 CLI parser。

    输入：
    无。

    输出：
    `argparse.ArgumentParser`，支持查看默认配置。

    关键边界：
    这里只保留安全只读动作，为后续 phase 追加命令组预留统一入口。
    """

    parser = argparse.ArgumentParser(
        prog="medical_tourism_os",
        description="Strategy-agnostic local operating system bootstrap",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="print safe local defaults as JSON",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    作用：
    解析命令并输出当前基础配置状态。

    输入：
    `argv` 为可选命令行参数序列。

    输出：
    进程退出码；成功时返回 0。

    关键边界：
    无论是否传参，都不得触发真实外部动作。
    """

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_config:
        print(json.dumps(SystemConfig.default().__dict__, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
