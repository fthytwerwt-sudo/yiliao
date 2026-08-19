"""
用途：
暴露 Phase 6 的离线接口层：CLI 与 loopback-only 本地 API。

上游：
`python -m medical_tourism_os`、测试和后续本地调试入口从这里导入接口对象。

下游：
委托服务层和 workflow 生成只读、安全、无外部副作用的响应。

边界：
接口层不自动启动服务、不开放公网绑定，也不触发现实业务动作。
"""

from medical_tourism_os.interfaces.cli import run_cli
from medical_tourism_os.interfaces.local_api import LocalApiApplication

__all__ = ["LocalApiApplication", "run_cli"]
