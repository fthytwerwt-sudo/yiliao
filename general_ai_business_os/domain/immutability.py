"""
用途：
为领域对象提供 JSON-compatible payload 的递归冻结与安全导出能力。

上游：
AuditEvent、StoredRecord 与未来经审核的配置版本在创建时调用这里复制输入。

下游：
`to_mutable_json` 为 JSON 编码和 Storage Port 产生新的可变快照。

边界：
本模块只保证容器别名和可变性边界；它不判断业务事实、审计字段是否合法，也不替代各领域入口的敏感数据校验。
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Mapping


def freeze_json(value: Any) -> Any:
    """
    递归复制并冻结 JSON-compatible 值。

    关键逻辑：
    frozen dataclass 只能禁止属性重新赋值，无法阻止嵌套 dict/list 被调用方改写。这里在
    领域边界复制全部容器，把 mapping 变为只读 proxy、sequence 变为 tuple，切断输入别名。
    """

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("json_float_must_be_finite")
        return value
    if isinstance(value, Mapping):
        frozen_mapping = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("json_mapping_key_must_be_string")
            frozen_mapping[key] = freeze_json(item)
        return MappingProxyType(frozen_mapping)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    raise ValueError("json_value_type_not_supported")


def freeze_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """冻结根 mapping；领域 payload 不允许用 list 或任意 Python 对象作为根。"""

    frozen = freeze_json(payload)
    if not isinstance(frozen, Mapping):
        raise ValueError("json_payload_must_be_mapping")
    return frozen


def to_mutable_json(value: Any) -> Any:
    """
    从冻结快照生成全新的 JSON-compatible 容器。

    返回值专门用于 JSON 编码和 API 输出；调用方修改它不会回写原领域对象，也不会影响
    随后由 Storage Port 读取的内部安全快照。
    """

    if isinstance(value, Mapping):
        return {key: to_mutable_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_mutable_json(item) for item in value]
    return value
