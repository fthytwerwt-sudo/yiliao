"""
用途：
提供不自动启动、只绑定本机 loopback 的 Local API 壳与统一路由清单。

上游：
CLI 调试、测试和未来本地 UI 可通过这里创建 HTTP server。

下游：
后续各 Agent 将在既有路由下注册真实的本地处理逻辑。

边界：
此阶段不对公网监听，也不执行外部动作；路由清单不等同于对应 Agent 已实现。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Tuple

from general_ai_business_os.config import SystemConfig


_ROUTE_INVENTORY = (
    "/config",
    "/content",
    "/leads",
    "/messages",
    "/crm",
    "/knowledge",
    "/experiments",
    "/metrics",
)


class LocalApiApplication:
    """Local API 工厂；只有调用者显式调用 server.serve_forever() 才会开始监听。"""

    def __init__(self, config: Optional[SystemConfig] = None) -> None:
        self._config = config or SystemConfig()
        self.is_running = False

    def route_inventory(self) -> Tuple[str, ...]:
        """返回系统目标路由，便于客户端发现能力而不伪造具体实现状态。"""

        return _ROUTE_INVENTORY

    def create_server(self) -> ThreadingHTTPServer:
        """
        创建 loopback-only HTTP server。

        关键边界：
        host 必须为 `127.0.0.1`；即使调用者传入其他配置也拒绝，避免本地调试接口意外暴露。
        """

        if self._config.api_host != "127.0.0.1":
            raise ValueError("local_api_requires_loopback_host")
        route_inventory = self.route_inventory()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - HTTP handler requires stdlib method name.
                payload = {"routes": route_inventory, "external_actions_allowed": False}
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

            def log_message(self, _format: str, *_args: object) -> None:
                """关闭 http.server 默认 stderr 日志，避免测试与调用者输出被污染。"""

        return ThreadingHTTPServer(("127.0.0.1", self._config.api_port), Handler)
