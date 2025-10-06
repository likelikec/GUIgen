"""
视觉LLM提示词模板与构建方法
将提示词与分析器逻辑解耦，便于维护与复用
"""
from typing import Dict, Any, List


# 旧方法已完全移除：请使用以下新方法
# - build_action_analysis_prompt_with_steps
# - build_action_analysis_prompt_no_steps


def build_action_analysis_prompt_with_steps(
    test_requirement: Dict[str, Any],
    current_step: int,
    max_steps: int,
    action_history: List[Dict[str, Any]]
) -> str:
    """构建：有步骤场景的操作分析提示词（严格提取）"""
    app_name = test_requirement.get("app", {}).get("name", "未知应用")
    objective = test_requirement.get("test_scenario", {}).get("objective", "")
    steps = test_requirement.get("test_scenario", {}).get("steps", [])
    test_data = test_requirement.get("test_scenario", {}).get("test_data", {})

    prompt = f"""你是一个专业的移动应用测试助手。请分析当前截图，并根据测试需求生成下一步操作指令（有步骤场景）。

测试信息：
- 应用名称：{app_name}
- 测试目标：{objective}
- 当前步骤：{current_step}/{max_steps}
"""

    # 必须包含步骤与（可能的）测试数据
    prompt += "\n测试步骤：\n"
    for i, step in enumerate(steps, 1):
        prompt += f"{i}. {step}\n"

    if test_data:
        prompt += f"\n测试数据：\n"
        for key, value in test_data.items():
            prompt += f"- {key}: {value}\n"

    if action_history:
        prompt += f"\n已执行的操作历史：\n"
        for action in action_history[-3:]:
            step_num = action.get("step")
            action_info = action.get("action", {})
            prompt += f"步骤{step_num}: {action_info.get('description', '未知操作')}\n"

    # 添加当前步骤的明确指示
    if current_step <= len(steps):
        current_step_desc = steps[current_step - 1]
        prompt += f"\n**重要：当前应该执行的步骤是第{current_step}步 - {current_step_desc}**\n"

    prompt += f"""
请分析当前截图，严格按照上面标注的"当前应该执行的步骤"来生成操作指令。

返回格式（JSON）：
{{
    "action_type": "click|input|swipe|back|home|wait|complete|error",
    "description": "操作描述",  // 只需清晰的目标控件或操作意图描述，不返回位置信息
    "text": "输入文本",  // 仅对 input 操作,输入完整的文本信息而不是一个字
    "swipe_direction": "up|down|left|right",  // 仅对 swipe 操作
    "wait_time": 2,  // 仅对 wait 操作，单位秒
    "reasoning": "选择此操作的原因",
    "success": true
}}

有步骤场景（提取规则）：
- 仅从上面的"测试步骤"与"测试数据"抽取下一步操作，不得创造未在步骤中出现的动作
- 输入文本时优先使用"测试数据"中的值
- **重要：只有当前步骤是最后一步且该步骤已完成时，才能返回"complete"操作**
- **如果当前步骤不是最后一步，绝对不能返回"complete"，必须执行当前步骤对应的具体操作**

严格要求：
- 仅输出上述JSON，不要包含任何额外文本或注释
    - click 不需要返回位置信息；由系统自动检测与定位
    - 输入动作必须提供 text
"""
    return prompt


def build_action_analysis_prompt_no_steps(
    test_requirement: Dict[str, Any],
    current_step: int,
    max_steps: int,
    action_history: List[Dict[str, Any]]
) -> str:
    """构建：无步骤场景的操作分析提示词（自主规划）"""
    app_name = test_requirement.get("app", {}).get("name", "未知应用")
    objective = test_requirement.get("test_scenario", {}).get("objective", "")

    prompt = f"""你是一个专业的移动应用测试助手。请分析当前截图，并根据测试目标生成下一步操作指令（无步骤场景）。

测试信息：
- 应用名称：{app_name}
- 测试目标：{objective}
- 当前步骤：{current_step}/{max_steps}
"""

    if action_history:
        prompt += f"\n已执行的操作历史：\n"
        for action in action_history[-3:]:
            step_num = action.get("step")
            action_info = action.get("action", {})
            prompt += f"步骤{step_num}: {action_info.get('description', '未知操作')}\n"

    prompt += f"""
请分析当前截图，结合“测试目标”自主推断下一步应该执行的操作。

返回格式（JSON）：
{{
    "action_type": "click|input|swipe|back|home|wait|complete|error",
    "description": "操作描述",  // 只需清晰的目标控件或操作意图描述，不返回位置信息
    "text": "输入文本",  // 仅对 input 操作
    "swipe_direction": "up|down|left|right",  // 仅对 swipe 操作
    "wait_time": 2,  // 仅对 wait 操作，单位秒
    "reasoning": "选择此操作的原因",
    "success": true
}}

无步骤场景（规划规则）：
- 根据“测试目标”和当前截图推断最合理的下一步操作

严格要求：
- 仅输出上述JSON，不要包含任何额外文本或注释
    - click 不需要返回位置信息；由系统自动检测与定位
    - 输入动作必须提供 text
"""

    return prompt

def build_system_prompt_for_action() -> str:
    """构建系统提示词：严格JSON；click 不返回位置信息"""
    return (
        "你是严格遵循指令格式的助手。所有回复必须仅包含一个JSON对象，字段与取值严格匹配用户消息中提供的架构。"
        "不要输出任何解释、注释、代码块围栏或额外文本。"
        "动作类型允许值为: click|input|swipe|back|home|wait|complete|error。"
        "对于 click，仅提供清晰的目标控件描述，不返回任何位置信息；位置由系统检测器决定。"
    )

def build_system_prompt_for_completion() -> str:
    """构建系统提示词：强制JSON用于完成度检查"""
    return (
        "你是严格遵循指令格式的助手。所有回复必须仅包含一个JSON对象，字段必须与用户消息要求一致。"
        "不要输出任何解释、注释、代码块围栏或额外文本。"
    )


def build_completion_check_prompt(test_requirement: Dict[str, Any]) -> str:
    """构建完成检查提示词"""
    objective = test_requirement.get("test_scenario", {}).get("objective", "")
    expected_result = test_requirement.get("test_scenario", {}).get("expected_result", "")
    success_criteria = test_requirement.get("test_scenario", {}).get("success_criteria", [])

    prompt = f"""你是一个专业的移动应用测试验证助手。请分析当前截图，判断测试是否已经完成。

测试目标：{objective}
"""

    # 仅当提供了预期结果与成功标准时，才加入这些段落
    if expected_result:
        prompt += f"\n预期结果：{expected_result}\n"
    if success_criteria:
        prompt += "\n成功标准：\n"
        for i, criteria in enumerate(success_criteria, 1):
            prompt += f"{i}. {criteria}\n"

    prompt += f"""
请仔细分析截图，判断测试是否已经达到预期结果和成功标准。

返回格式（JSON）：
{{
    "completed": true/false,
    "success": true/false,
    "confidence": 0.95,  // 置信度 0-1
    "reasoning": "判断理由",
    "achieved_criteria": ["已达成的成功标准"],
    "missing_criteria": ["未达成的成功标准"],
    "next_suggestion": "如果未完成，建议下一步操作"
}}

注意事项：
1. 仔细检查截图中是否出现了预期的结果
2. 若未提供明确成功标准，请依据目标与界面状态综合判断
3. 逐一验证提供的成功标准（如有）是否达成
4. 如果有任何疑问，倾向于返回未完成，并给出下一步建议
5. 提供详细的判断理由
"""
    
    return prompt