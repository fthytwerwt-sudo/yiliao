"""
用途：
提供 General AI Business Operating System 的本地命令行入口。

上游：
开发者或测试调用 `python -m general_ai_business_os system init`。

下游：
CLI 创建本地 SQLite 状态并输出可机读的安全运行状态。

边界：
当前只支持本地 `system init`；业务配置导入属于 Application Plugin，不能经 Core CLI 注入。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from general_ai_business_os.config import SystemConfig
from general_ai_business_os.storage.sqlite_store import SqliteStore


def _build_parser() -> argparse.ArgumentParser:
    """构建可扩展的命令树；后续 Phase 会在明确子命令下增加实际能力。"""

    parser = argparse.ArgumentParser(prog="general-ai-business-os")
    root_commands = parser.add_subparsers(dest="command", required=True)
    system = root_commands.add_parser("system")
    system_commands = system.add_subparsers(dest="system_command", required=True)
    init = system_commands.add_parser("init")
    init.add_argument("--state-root", required=True)
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """
    作用：
    执行 CLI 指定命令并输出结构化 JSON。

    关键边界：
    `system init` 只创建本地 SQLite schema；输出必须始终说明 external actions 没有被开启。
    """

    arguments = _build_parser().parse_args(list(argv) if argv is not None else None)
    if arguments.command == "system" and arguments.system_command == "init":
        config = SystemConfig(state_root=Path(arguments.state_root))
        store = SqliteStore(config.sqlite_path())
        store.migrate()
        print(
            json.dumps(
                {
                    "status": "initialized",
                    "state_root": str(config.resolved_state_root()),
                    "external_actions_allowed": config.external_actions_allowed,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    raise AssertionError("unreachable_cli_command")
