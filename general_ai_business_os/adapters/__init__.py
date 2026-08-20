"""外部能力 Port 与 Mock 实现入口。"""

from general_ai_business_os.adapters.base import BaseAdapter
from general_ai_business_os.adapters.mock import MockAdapter

__all__ = ("BaseAdapter", "MockAdapter")
