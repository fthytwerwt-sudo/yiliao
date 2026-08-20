"""
用途：
提供不自动启动、只绑定本机 loopback 的 General AI Core 状态接口。

上游：
CLI 调试、测试和未来本地 UI 可通过这里创建 HTTP server。

下游：
未来 Application Plugin 可在自己的适配器中注册业务路由；Core 只暴露自身状态。

边界：
此阶段不对公网监听，也不执行外部动作；Core 不枚举或导入业务配置、客户、CRM 或内容能力。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Tuple

from general_ai_business_os.config import SystemConfig


_ROUTE_INVENTORY = ("/",)


class LocalApiApplication:
    """Local API 工厂；只有调用者显式调用 server.serve_forever() 才会开始监听。"""

    def __init__(self, config: Optional[SystemConfig] = None) -> None:
        self._config = config or SystemConfig()
        self.is_running = False

    def route_inventory(self) -> Tuple[str, ...]:
        """返回 Core 已实现的状态路由；业务路由必须由 Application Plugin 自行拥有。"""

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

        def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
            """统一返回本地 JSON，避免 handler 各自形成不一致的错误/状态语义。"""

            handler.send_response(status)
            handler.send_header("Content-Type", "application/json; charset=utf-8")
            handler.end_headers()
            handler.wfile.write(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - HTTP handler requires stdlib method name.
                if self.path == "/":
                    send_json(
                        self,
                        200,
                        {
                            "routes": route_inventory,
                            "route_status": "core_runtime_status",
                            "external_actions_allowed": False,
                        },
                    )
                    return
                send_json(self, 404, {"status": "blocked", "reason": "route_not_found"})

            def do_POST(self) -> None:  # noqa: N802 - HTTP handler requires stdlib method name.
                send_json(self, 404, {"status": "blocked", "reason": "route_not_found"})

            def log_message(self, _format: str, *_args: object) -> None:
                """关闭 http.server 默认 stderr 日志，避免测试与调用者输出被污染。"""

        return ThreadingHTTPServer(("127.0.0.1", self._config.api_port), Handler)
