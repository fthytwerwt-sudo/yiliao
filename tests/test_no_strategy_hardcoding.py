"""静态回归：核心 Python 不能写入现实业务战略，也不能用空实现冒充完成。"""

from __future__ import annotations

import ast
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE_PYTHON_FILES = (
    "medical_tourism_os/__main__.py",
    "medical_tourism_os/interfaces/__init__.py",
    "medical_tourism_os/interfaces/cli.py",
    "medical_tourism_os/interfaces/local_api.py",
    "medical_tourism_os/services/learning_loop.py",
    "medical_tourism_os/workflows/weekly_review.py",
    "medical_tourism_os/workflows/e2e_scenario.py",
    "medical_tourism_os/services/business_core.py",
    "medical_tourism_os/services/content_interaction.py",
    "medical_tourism_os/services/data_governance.py",
    "medical_tourism_os/services/risk_router.py",
)

# 这里只拦“现实业务写死”的具体名词，而不是抽象领域词。
FORBIDDEN_PATTERNS = (
    re.compile(r"\bchina\b", re.IGNORECASE),
    re.compile(r"\bthailand\b", re.IGNORECASE),
    re.compile(r"\bsingapore\b", re.IGNORECASE),
    re.compile(r"\bdubai\b", re.IGNORECASE),
    re.compile(r"\btiktok\b", re.IGNORECASE),
    re.compile(r"\binstagram\b", re.IGNORECASE),
    re.compile(r"\bamazon\b", re.IGNORECASE),
    re.compile(r"\bhospital\b", re.IGNORECASE),
    re.compile(r"医院"),
    re.compile(r"(?:USD|CNY|RMB|EUR|SGD|AED)\s*\d", re.IGNORECASE),
    re.compile(r"[$¥€]\s*\d"),
)


def _iter_non_docstring_strings(tree: ast.AST) -> list[str]:
    """收集非 docstring 字符串常量，避免把说明文档误算成业务硬编码。"""

    collected: list[str] = []
    docstring_nodes: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstring_nodes.add(id(first.value))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstring_nodes:
            collected.append(node.value)
    return collected


def _class_body_is_placeholder(class_node: ast.ClassDef) -> bool:
    """判断 class 是否只有 docstring / pass / TODO，占位而无真实实现。"""

    meaningful_nodes = []
    for item in class_node.body:
        if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
            continue
        meaningful_nodes.append(item)
    if not meaningful_nodes:
        return True
    if all(isinstance(item, ast.Pass) for item in meaningful_nodes):
        return True
    return False


def _is_exception_marker(class_node: ast.ClassDef) -> bool:
    """跳过仅用于声明错误类型的异常类，这类空壳是合法 Python 模式。"""

    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id.endswith("Error"):
            return True
    return False


class NoStrategyHardcodingTests(unittest.TestCase):
    """锁住 Phase 5–7 不写入现实国家/平台/医院/价格，也不能交空壳模块。"""

    def test_required_phase5_to_phase7_modules_exist(self) -> None:
        """新增 learning / interface / e2e 模块必须真实存在。"""

        missing = [relative_path for relative_path in CORE_PYTHON_FILES if not (ROOT / relative_path).exists()]
        self.assertEqual([], missing)

    def test_core_python_has_no_real_world_strategy_hardcoding(self) -> None:
        """核心 Python 不得把现实业务路线、平台、医院或真实价格写死进去。"""

        violations: list[str] = []
        for relative_path in CORE_PYTHON_FILES:
            path = ROOT / relative_path
            if not path.exists():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for value in _iter_non_docstring_strings(tree):
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(value):
                        violations.append(f"{relative_path}: {value}")
        self.assertEqual([], violations)

    def test_key_modules_are_not_placeholder_pass_or_todo_shells(self) -> None:
        """关键模块必须有真实实现，不能只剩空 class、pass 或 TODO。"""

        placeholder_violations: list[str] = []
        todo_violations: list[str] = []
        phase_files = (
            "medical_tourism_os/interfaces/cli.py",
            "medical_tourism_os/interfaces/local_api.py",
            "medical_tourism_os/services/learning_loop.py",
            "medical_tourism_os/workflows/weekly_review.py",
            "medical_tourism_os/workflows/e2e_scenario.py",
        )
        for relative_path in phase_files:
            path = ROOT / relative_path
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            if "TODO" in source:
                todo_violations.append(relative_path)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ClassDef)
                    and not _is_exception_marker(node)
                    and _class_body_is_placeholder(node)
                ):
                    placeholder_violations.append(f"{relative_path}:{node.name}")
        self.assertEqual([], placeholder_violations)
        self.assertEqual([], todo_violations)


if __name__ == "__main__":
    unittest.main()
