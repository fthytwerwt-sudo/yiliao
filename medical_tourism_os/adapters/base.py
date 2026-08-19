"""
用途：
定义外部 adapter 的统一基础接口。

上游：
future publishing/sync 服务会通过这里操作不同 adapter。

下游：
mock.py 与未来真实 adapter 实现继承该基类并返回统一结果结构。

边界：
基础接口只描述调用合同，不保存凭据，不直接接入任何现实平台。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Dict

from medical_tourism_os.domain.entities import AdapterResult


class BaseAdapter(ABC):
    """
    作用：
    约束所有 adapter 的最小行为接口。

    输入：
    `enabled` 表示该 adapter 是否被显式启用。

    输出：
    子类通过 `publish()` 返回统一的 `AdapterResult`。

    关键边界：
    adapter 层必须明确表达 dry-run 与 executed 的差异，不能用“静默不做事”掩盖权限状态。
    """

    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled

    @abstractmethod
    def publish(self, payload: Dict[str, Any]) -> AdapterResult:
        """执行或模拟一次发布动作。"""

    @staticmethod
    def serialize_result(result: AdapterResult) -> Dict[str, Any]:
        """把 adapter 结果转成可 JSON 编码的字典。"""

        return asdict(result)
