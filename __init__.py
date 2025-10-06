"""
GUIgen - 视觉 LLM 驱动的移动 GUI 自动化测试（简化版）

最小化包初始化：仅提供版本信息与核心便捷导出。
"""

__version__ = "1.1.0"
__author__ = "AgentExec Team"
__description__ = "Visual LLM-driven mobile GUI automation (simplified)."


from .core.device_manager import DeviceManager
from .core.llm_interface import LLMInterface
from .core.visual_llm import VisualLLMAnalyzer
from .core.test_engine import TestEngine

__all__ = [
    "DeviceManager",
    "LLMInterface",
    "VisualLLMAnalyzer",
    "TestEngine",
]