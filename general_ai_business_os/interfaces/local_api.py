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
from pathlib import Path
from typing import Optional, Tuple

from general_ai_business_os.business_config.contracts import BusinessConfigError
from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
from general_ai_business_os.config import SystemConfig
from general_ai_business_os.storage.sqlite_store import SqliteStore


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

    def __init__(
        self,
        config: Optional[SystemConfig] = None,
        config_pipeline: Optional[BusinessConfigPipeline] = None,
    ) -> None:
        self._config = config or SystemConfig()
        self._config_pipeline = config_pipeline or BusinessConfigPipeline(SqliteStore(self._config.sqlite_path()))
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
        config_pipeline = self._config_pipeline

        def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
            """统一返回本地 JSON，避免 handler 各自形成不一致的错误/状态语义。"""

            handler.send_response(status)
            handler.send_header("Content-Type", "application/json; charset=utf-8")
            handler.end_headers()
            handler.wfile.write(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - HTTP handler requires stdlib method name.
                if self.path in ("/", "/config"):
                    send_json(
                        self,
                        200,
                        {
                            "routes": route_inventory,
                            "route_status": "config_import_available" if self.path == "/config" else "inventory_only",
                            "external_actions_allowed": False,
                        },
                    )
                    return
                send_json(self, 404, {"status": "blocked", "reason": "route_not_found"})

            def do_POST(self) -> None:  # noqa: N802 - HTTP handler requires stdlib method name.
                if self.path != "/config":
                    send_json(self, 404, {"status": "blocked", "reason": "route_not_found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(body, dict) or not isinstance(body.get("package_path"), str):
                        raise ValueError("config_package_path_required")
                    package = config_pipeline.import_package(Path(body["package_path"]))
                except (BusinessConfigError, ValueError, json.JSONDecodeError) as error:
                    send_json(self, 400, {"status": "blocked", "reason": str(error)})
                    return
                send_json(
                    self,
                    201,
                    {
                        "status": "imported",
                        "business_id": package.manifest.business_id,
                        "config_version": package.manifest.config_version,
                        "review_status": package.manifest.review_status.value,
                        "external_actions_allowed": False,
                    },
                )

            def log_message(self, _format: str, *_args: object) -> None:
                """关闭 http.server 默认 stderr 日志，避免测试与调用者输出被污染。"""

        return ThreadingHTTPServer(("127.0.0.1", self._config.api_port), Handler)
