
import base64
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from .llm_interface import LLMInterface
from .prompts_visual import (
    build_action_analysis_prompt_with_steps,
    build_action_analysis_prompt_no_steps,
    build_completion_check_prompt,
    build_system_prompt_for_action,
    build_system_prompt_for_completion,
)


class VisualLLMAnalyzer:
    """视觉LLM分析器"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化视觉LLM分析器
        
        Args:
            llm_interface: LLM接口实例
        """
        self.llm_interface = llm_interface
        self.action_history = []  # 操作历史记录
        
    def analyze_screenshot_for_action(
        self, 
        screenshot_path: str, 
        test_requirement: Dict[str, Any],
        current_step: int,
        max_steps: int
    ) -> Dict[str, Any]:
        """
        分析截图并生成下一步操作指令
        
        Args:
            screenshot_path: 截图文件路径
            test_requirement: 测试需求
            current_step: 当前步骤数
            max_steps: 最大步骤数
            
        Returns:
            操作指令字典
        """
        try:
            # 构建分析提示：先判断是否提供了步骤信息
            steps = test_requirement.get("test_scenario", {}).get("steps", [])
            if steps:
                prompt = build_action_analysis_prompt_with_steps(
                    test_requirement, current_step, max_steps, self.action_history
                )
            else:
                prompt = build_action_analysis_prompt_no_steps(
                    test_requirement, current_step, max_steps, self.action_history
                )
            
            # 获取LLM分析结果（第一阶段：粗定位）
            system_prompt = build_system_prompt_for_action()
            print("智能分析当前截图中...")
            response = self.llm_interface.get_action_decision(
                screenshot_path, prompt, system_prompt
            )
            print(f"Agent分析响应: {response}")

            action_result = self._parse_action_response(response)

            # 第二阶段：细化定位（仅优化目标描述），并带重试
            refine_attempts = 0
            if action_result.get("action_type") == "click":
                # 仅在点击场景尝试细化
                while refine_attempts < 2:
                    refine_attempts += 1
                    # 构造细化提示词（不再请求位置信息，只优化目标描述）
                    refine_prompt = (
                        "请更清晰地描述要点击的目标控件（例如按钮文本、图标含义、附近标签），并严格返回规范化JSON。\n"
                        "要求：\n"
                        "1) 返回 action_type 与 description；\n"
                        "2) 如当前界面不宜点击，则返回 wait 并简述原因；\n"
                        "3) 不返回任何位置信息。\n"
                    )

                    # 组合为多轮消息：上一轮为助手消息，本轮为用户细化请求
                    coarse_user_msg = {"image": screenshot_path, "text": prompt}
                    refine_user_msg = {"image": screenshot_path, "text": refine_prompt}
                    messages = self.llm_interface.build_messages(
                        [coarse_user_msg, refine_user_msg],
                        system_prompt,
                        assistant_messages=[response]
                    )
                    try:
                        refine_resp = self.llm_interface.chat_completion(messages)
                        refine_content = refine_resp.get("content", "")
                        print(f"Agent细化响应: {refine_content}")
                        refined = self._parse_action_response(refine_content)
                        # 若返回为合法点击（有动作与描述），则替换结果并停止细化
                        act = refined.get("action_type")
                        if act == "click" and isinstance(refined.get("description"), str):
                            action_result = refined
                            break
                        else:
                            # 将上一轮响应加入历史，以便后续纠偏
                            self.action_history.append({
                                "step": current_step,
                                "screenshot": screenshot_path,
                                "action": refined,
                                "timestamp": self._get_timestamp(),
                                "phase": "refine_attempt"
                            })
                    except Exception as e:
                        # 细化失败则继续重试
                        pass
            
            # 记录操作历史
            self.action_history.append({
                "step": current_step,
                "screenshot": screenshot_path,
                "action": action_result,
                "timestamp": self._get_timestamp()
            })
            
            return action_result
            
        except Exception as e:
            return {
                "action_type": "error",
                "error": str(e),
                "success": False
            }
    
    def check_test_completion(
        self, 
        screenshot_path: str, 
        test_requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查测试是否完成
        
        Args:
            screenshot_path: 当前截图路径
            test_requirement: 测试需求
            
        Returns:
            完成检查结果
        """
        try:
            # 构建完成检查提示（解耦到独立提示词模块）
            prompt = build_completion_check_prompt(test_requirement)
            
            # 获取LLM检查结果
            system_prompt = build_system_prompt_for_completion()
            response = self.llm_interface.check_test_completion(
                screenshot_path, prompt, system_prompt
            )
            
            # 解析响应
            completion_result = self._parse_completion_response(response)
            
            return completion_result
            
        except Exception as e:
            return {
                "completed": False,
                "success": False,
                "error": str(e)
            }

    # 兼容旧接口：提供 analyze_and_generate_action 的包装以适配 TestEngine
    def analyze_and_generate_action(
        self,
        screenshot_path: str,
        test_requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """兼容旧接口，自动推断当前步数并生成下一步操作"""
        current_step = len(self.action_history) + 1
        steps = test_requirement.get("test_scenario", {}).get("steps", [])
        max_steps = len(steps) if isinstance(steps, list) and steps else current_step + 5
        return self.analyze_screenshot_for_action(
            screenshot_path,
            test_requirement,
            current_step,
            max_steps
        )

    # 兼容旧接口：提供 perform_final_check 的包装以适配 TestEngine
    def perform_final_check(
        self,
        screenshot_path: str,
        test_requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """兼容旧接口，委托到 check_test_completion"""
        return self.check_test_completion(screenshot_path, test_requirement)
    
    def _build_completion_check_prompt(self, test_requirement: Dict[str, Any]) -> str:
        """兼容旧接口：委托到 prompts_visual 模块"""
        return build_completion_check_prompt(test_requirement)
    
    def _parse_action_response(self, response: str) -> Dict[str, Any]:
        """解析操作响应"""
        # 先尝试直接解析；失败则提取并规范化JSON
        raw = response.strip()
        # 去除代码块围栏
        if raw.startswith("```"):
            raw = raw.strip("`")
        raw = raw.replace("```json", "").replace("```", "").strip()

        # 尝试直接解析并做规范化
        if raw.startswith('{'):
            try:
                direct_parsed = json.loads(raw)
                if isinstance(direct_parsed, dict):
                    result = dict(direct_parsed)
                    if "action_type" not in result:
                        if isinstance(result.get("action"), str):
                            result["action_type"] = result["action"]
                        elif isinstance(result.get("type"), str):
                            result["action_type"] = result["type"]
                    # 统一 target 到 description
                    if not result.get("description") and isinstance(result.get("target"), str):
                        result["description"] = result.get("target")
                    act = result.get("action_type")
                    if act == "click":
        # ScenGen：不再要求返回位置信息；仅保留描述，位置由检测器决定
                        result.setdefault("description", result.get("description", ""))
                    elif act == "input":
                        if not result.get("text"):
                            result["action_type"] = "wait"
                            result["reasoning"] = "LLM未提供输入文本，暂时等待"
                            result["wait_time"] = result.get("wait_time", 2)
                            result["success"] = False
                    result.setdefault("description", "")
                    result.setdefault("success", True)  # 能够解析出有效操作就认为成功
                    return result
            except Exception:
                pass

        # 提取第一个JSON对象子串（通过括号配对）
        def _extract_json(text: str) -> Optional[str]:
            start_idx = text.find('{')
            if start_idx == -1:
                return None
            depth = 0
            for i in range(start_idx, len(text)):
                c = text[i]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start_idx:i+1]
            return None

        candidate = _extract_json(raw)
        if candidate:
            # 尝试修复常见错误：单引号、尾随逗号
            normalized = candidate
            if '"' not in normalized and "'" in normalized:
                normalized = normalized.replace("'", '"')
            # 移除可能存在的行内注释（简易处理）
            normalized = '\n'.join([line for line in normalized.split('\n') if not line.strip().startswith('//')])
            # 去除可能的尾随逗号
            normalized = normalized.replace(',\n}', '\n}')
            normalized = normalized.replace(', }', ' }')
            try:
                parsed = json.loads(normalized)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                # 规范化字段，兼容非标准键名
                result = dict(parsed)
                if "action_type" not in result:
                    if isinstance(result.get("action"), str):
                        result["action_type"] = result["action"]
                    elif isinstance(result.get("type"), str):
                        result["action_type"] = result["type"]
                # 统一 target 到 description
                if not result.get("description") and isinstance(result.get("target"), str):
                    result["description"] = result.get("target")
                # 对关键动作进行校验与回退
                act = result.get("action_type")
                if act == "click":
        # ScenGen：不再要求返回位置信息；仅保留描述，位置由检测器决定
                    result.setdefault("description", result.get("description", ""))
                elif act == "input":
                    if not result.get("text"):
                        result["action_type"] = "wait"
                        result["reasoning"] = "LLM未提供输入文本，暂时等待"
                        result["wait_time"] = result.get("wait_time", 2)
                        result["success"] = False
                # 填充缺省字段
                result.setdefault("description", "")
                result.setdefault("success", True)  # 能够解析出有效操作就认为成功
                return result

        # 关键词回退（确保不会报错）
        response_lower = raw.lower()
        result = {
            "action_type": "wait",
            "description": "LLM响应解析失败，等待处理",
            "wait_time": 2,
            "success": False,
            "reasoning": "响应格式不正确"
        }
        if "click" in response_lower:
            result["action_type"] = "click"
            result["reasoning"] = "根据关键词推断为点击，位置由检测器决定"
        elif "input" in response_lower or "type" in response_lower:
            result["action_type"] = "input"
        elif "swipe" in response_lower or "scroll" in response_lower:
            result["action_type"] = "swipe"
        elif "back" in response_lower:
            result["action_type"] = "back"
        elif "complete" in response_lower or "finish" in response_lower:
            result["action_type"] = "complete"
        return result
    
    def _parse_completion_response(self, response: str) -> Dict[str, Any]:
        """解析完成检查响应"""
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
        raw = raw.replace("```json", "").replace("```", "").strip()

        if raw.startswith('{'):
            try:
                return json.loads(raw)
            except Exception:
                pass

        def _extract_json(text: str) -> Optional[str]:
            start_idx = text.find('{')
            if start_idx == -1:
                return None
            depth = 0
            for i in range(start_idx, len(text)):
                c = text[i]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start_idx:i+1]
            return None

        candidate = _extract_json(raw)
        if candidate:
            normalized = candidate
            if '"' not in normalized and "'" in normalized:
                normalized = normalized.replace("'", '"')
            normalized = '\n'.join([line for line in normalized.split('\n') if not line.strip().startswith('//')])
            normalized = normalized.replace(',\n}', '\n}')
            normalized = normalized.replace(', }', ' }')
            try:
                parsed = json.loads(normalized)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                return parsed

        # 关键词回退
        response_lower = raw.lower()
        completed = any(word in response_lower for word in [
            "completed", "finished", "success", "达成", "完成", "成功"
        ])
        return {
            "completed": completed,
            "success": completed,
            "confidence": 0.5,
            "reasoning": "基于关键词判断",
            "achieved_criteria": [],
            "missing_criteria": [],
            "next_suggestion": "请检查响应格式"
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.action_history.copy()
    
    def clear_history(self):
        """清空操作历史"""
        self.action_history.clear()
    
    def save_test_report(self, save_path: str, test_requirement: Dict[str, Any], final_result: Dict[str, Any]):
        """
        保存测试报告
        
        Args:
            save_path: 保存路径
            test_requirement: 测试需求
            final_result: 最终测试结果
        """
        try:
            report = {
                "test_info": {
                    "test_id": test_requirement.get("test_id"),
                    "test_name": test_requirement.get("test_name"),
                    "app_name": test_requirement.get("app", {}).get("name"),
                    "objective": test_requirement.get("test_scenario", {}).get("objective")
                },
                "execution_summary": {
                    "total_steps": len(self.action_history),
                    "completed": final_result.get("completed", False),
                    "success": final_result.get("success", False),
                    "confidence": final_result.get("confidence", 0.0)
                },
                "action_history": self.action_history,
                "final_result": final_result,
                "timestamp": self._get_timestamp()
            }
            
            # 确保保存目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存报告
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存测试报告失败: {e}")