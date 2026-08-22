"""暴露只使用 synthetic fixtures 且永不产生真实外部动作的 Mock Adapters。"""

from medical_tourism_os.acquisition.adapters.mock import MockDirectoryProvider, MockEmailProvider

__all__ = ["MockDirectoryProvider", "MockEmailProvider"]
