"""验证 Memory Interface 的值隔离，避免 Agent 运行快照被调用方可变对象污染。"""

from __future__ import annotations

import unittest

from general_ai_business_os.memory import InMemoryStore


class MemoryInterfaceTests(unittest.TestCase):
    """Memory Store 是 Runtime 边界；保存与读取都必须返回独立快照。"""

    def test_nested_values_cannot_mutate_memory_through_put_or_get(self) -> None:
        """嵌套 Mapping 是常见状态结构，浅拷贝会让调用方绕过 Memory 接口改写内部状态。"""

        store = InMemoryStore()
        original = {"nested": {"status": "INITIAL"}}
        store.put("TEST_MEMORY", original)
        original["nested"]["status"] = "MUTATED_AFTER_PUT"

        retrieved = store.get("TEST_MEMORY")
        self.assertEqual({"nested": {"status": "INITIAL"}}, retrieved)

        assert retrieved is not None
        retrieved["nested"]["status"] = "MUTATED_AFTER_GET"
        self.assertEqual({"nested": {"status": "INITIAL"}}, store.get("TEST_MEMORY"))


if __name__ == "__main__":
    unittest.main()
