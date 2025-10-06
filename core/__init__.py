"""
仅声明现有子模块，避免初始化阶段触发不存在模块的 ImportError。
"""

__all__ = [
    "device_manager",
    "llm_interface",
    "prompts_visual",
    "test_engine",
    "visual_llm",
]