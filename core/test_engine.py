
import json
import os
import time
import re
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
from .element import Element
from .device_manager import DeviceManager
from .llm_interface import LLMInterface
from .visual_llm import VisualLLMAnalyzer


class TestEngine:
    """测试执行引擎"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化测试引擎
        
        Args:
            config: 配置参数
        """
        self.raw_config = config or {}
        self.device_manager = None
        self.llm_interface = None
        self.visual_analyzer = None
        self.current_test = None
        self.test_results = []
        self.step_count = 0
        self.max_retry_count = 3

        # 添加点击历史记录，用于检测重复点击
        self.click_history = []  # 存储最近的点击坐标
        self.max_click_history = 5  # 最多记录5次点击
        self.repeat_click_threshold = 2  # 连续2次相同位置视为重复点击（降低阈值）
        self.last_screenshot_hash = None  # 用于检测界面变化

        # 强制使用 config.json 的 test_engine 配置，不再使用默认值
        engine_conf = self.raw_config.get("test_engine", {}) if isinstance(self.raw_config, dict) else {}
        required_keys = [
            "max_steps",
            "step_timeout",
            "screenshot_interval",
            "retry_count",
            "screenshots_dir",
            "reports_dir",
        ]
        missing = [k for k in required_keys if k not in engine_conf]
        if missing:
            raise ValueError(f"配置文件缺少 test_engine 必填项: {', '.join(missing)}")
        self.config = engine_conf
    
    def initialize(self, device_id: Optional[str] = None, llm_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化测试引擎组件
        
        Args:
            device_id: 设备ID
            llm_config: LLM配置
            
        Returns:
            是否初始化成功
        """
        try:
            # 初始化设备管理器（优先使用命令行指定，其次使用config.json的device.default_device_id）
            device_conf = self.raw_config.get("device", {})
            resolved_device_id = device_id if device_id else device_conf.get("default_device_id")
            self.device_manager = DeviceManager(resolved_device_id, device_config=device_conf)
            print(f"设备连接成功: {self.device_manager.device_id}")
            
            # 初始化LLM接口（强制使用config.json的llm配置，除非显式传入）
            llm_conf = llm_config if llm_config is not None else self.raw_config.get("llm", {})
            self.llm_interface = LLMInterface(
                api_key=llm_conf.get("api_key"),
                base_url=llm_conf.get("base_url"),
                model=llm_conf.get("model"),
                temperature=llm_conf.get("temperature"),
                max_tokens=llm_conf.get("max_tokens"),
                timeout=llm_conf.get("timeout"),
            )
            
            # 初始化视觉分析器
            self.visual_analyzer = VisualLLMAnalyzer(self.llm_interface)
            return True
            
        except Exception as e:
            print(f"测试引擎初始化失败: {e}")
            return False
    
    def load_test_requirement(self, json_file_path: str) -> bool:
        """
        加载测试需求文件
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            是否加载成功
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.current_test = json.load(f)
            
            # 根据测试步骤数量自动调整max_steps
            test_scenario = self.current_test.get('test_scenario', {})
            steps = test_scenario.get('steps', [])
            if isinstance(steps, list) and len(steps) > 0:
                # 有明确步骤的测试，使用步骤数量作为max_steps
                self.config['max_steps'] = len(steps)
                print(f"根据测试步骤数量自动设置max_steps为: {len(steps)}")
            else:
                # 没有明确步骤的测试，使用默认值
                default_max_steps = 10  # 可以根据需要调整默认值
                self.config['max_steps'] = default_max_steps
                print(f"使用默认max_steps: {default_max_steps}")
            
            print(f"测试需求加载成功: {self.current_test.get('test_name', '未知测试')}")
            return True
            
        except Exception as e:
            print(f"加载测试需求失败: {e}")
            return False
    
    def execute_test(self) -> Dict[str, Any]:
        """
        执行测试
        
        Returns:
            测试结果
        """
        if not self.current_test:
            return {
                "success": False,
                "error": "未加载测试需求",
                "steps": [],
                "final_check": None
            }
        
        try:
            # 启动应用
            if not self._launch_app():
                return {
                    "success": False,
                    "error": "应用启动失败",
                    "steps": [],
                    "final_check": None
                }
            
            # 执行测试步骤
            steps_result = self._execute_test_steps()
            
            # 执行最终检查
            final_check = self._perform_final_check()
            
            # 生成测试结果
            test_result = {
                "success": steps_result["success"] and final_check["success"],
                "error": steps_result.get("error") or final_check.get("error"),
                "steps": steps_result["steps"],
                "final_check": final_check,
                "test_name": self.current_test.get("test_name", "未知测试"),
                "total_steps": len(steps_result["steps"])
            }
            
            # 保存测试报告
            self._save_test_report(test_result)
            
            return test_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"测试执行异常: {e}",
                "steps": [],
                "final_check": None
            }
    
    def _launch_app(self) -> bool:
        """启动应用"""
        app_info = self.current_test.get("app_info", {})
        package_name = app_info.get("package_name")
        activity_name = app_info.get("activity_name")

        # 兼容 test_requirements.json 使用的 "app" 字段结构
        if not package_name or not activity_name:
            app = self.current_test.get("app", {})
            # 映射为 DeviceManager 所需字段
            package_name = package_name or app.get("package")
            activity_name = activity_name or app.get("launch_activity")

        if not package_name or not activity_name:
            print("应用信息不完整（缺少包名或启动Activity）。请在 app 或 app_info 中填写 package/launch_activity 或 package_name/activity_name。")
            return False
        
        print(f"启动应用: {package_name}/{activity_name}")
        success = self.device_manager.launch_app(package_name, activity_name)
        
        if success:
            # 启动后等待应用加载
            time.sleep(self.device_manager.operation_delay * 2)
            print("应用启动成功")
        else:
            print("应用启动失败")
        
        return success
    
    def _execute_test_steps(self) -> Dict[str, Any]:
        """执行测试步骤"""
        steps = []
        max_steps = self.config.get("max_steps", 20)
        step_timeout = self.config.get("step_timeout", 30)
        
        self.step_count = 0
        
        while self.step_count < max_steps:
            self.step_count += 1
            step_start_time = time.time()
            
            print(f"\n=== 执行步骤 {self.step_count} ===")
            
            # 截图
            screenshot_path = self._take_screenshot(self.step_count, "before")
            if not screenshot_path:
                steps.append({
                    "step": self.step_count,
                    "success": False,
                    "error": "截图失败",
                    "action": None,
                    "screenshot": None,
                    "duration": time.time() - step_start_time
                })
                break
            
            # 视觉分析和动作生成
            try:
                print("智能分析中...")
                action_result = self.visual_analyzer.analyze_and_generate_action(
                    screenshot_path, 
                    self.current_test
                )
                
                if not action_result:
                    steps.append({
                        "step": self.step_count,
                        "success": False,
                        "error": "LLM分析失败",
                        "action": None,
                        "screenshot": screenshot_path,
                        "duration": time.time() - step_start_time
                    })
                    break
                
                print(f"Agent建议操作: {action_result}")

                # 执行操作（带重试机制）
                # 附带当前截图路径用于几何对齐
                action_result["screenshot_path"] = screenshot_path
                action_success = self._execute_action_with_retry(action_result)
                
                # 记录步骤结果
                step_result = {
                    "step": self.step_count,
                    "success": action_success,
                    "action": action_result,
                    "screenshot": screenshot_path,
                    "duration": time.time() - step_start_time
                }
                
                if not action_success:
                    step_result["error"] = "操作执行失败"
                
                steps.append(step_result)
                
                # 检查是否完成
                if action_result.get("action_type") == "complete":
                    print("Agent测试完成")
                    break
                
                # 步骤间延迟
                time.sleep(self.config.get("screenshot_interval", 2))
                
                # 检查超时
                if time.time() - step_start_time > step_timeout:
                    steps.append({
                        "step": self.step_count + 1,
                        "success": False,
                        "error": "步骤执行超时",
                        "action": None,
                        "screenshot": None,
                        "duration": step_timeout
                    })
                    break
                    
            except Exception as e:
                steps.append({
                    "step": self.step_count,
                    "success": False,
                    "error": f"步骤执行异常: {e}",
                    "action": None,
                    "screenshot": screenshot_path,
                    "duration": time.time() - step_start_time
                })
                break
        
        # 判断整体成功
        success = len(steps) > 0 and any(step.get("success", False) for step in steps)
        
        return {
            "success": success,
            "steps": steps,
            "error": None if success else "所有步骤都失败了"
        }
    
    def _take_screenshot(self, step: int, suffix: str = "") -> Optional[str]:
        """截取屏幕截图"""
        try:
            screenshots_dir = self.config.get("screenshots_dir", "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            test_name = self.current_test.get("test_name", "unknown_test")
            # 文件名安全化：移除中文及非常规字符，仅保留 ASCII 字母、数字、下划线、连字符
            safe_test_name = ''.join(c if c.isascii() and (c.isalnum() or c in ['_', '-']) else '_' for c in test_name)
            # 精简多余的下划线并去除首尾下划线/连字符
            safe_test_name = re.sub(r'_+', '_', safe_test_name).strip('_-') or 'screenshot'
            timestamp = int(time.time())
            
            if suffix:
                filename = f"{safe_test_name}_step_{step}_{suffix}_{timestamp}.png"
            else:
                filename = f"{safe_test_name}_step_{step}_{timestamp}.png"
            
            screenshot_path = os.path.join(screenshots_dir, filename)
            
            if self.device_manager.take_screenshot(screenshot_path):
                print(f"截图保存: {screenshot_path}")
                return screenshot_path
            else:
                print("截图失败")
                return None
                
        except Exception as e:
            print(f"截图异常: {e}")
            return None
    
    def _execute_action_with_retry(self, action_result: Dict[str, Any]) -> bool:
        """执行操作（带重试机制）"""
        action_type = action_result.get("action_type", "")
        
        for attempt in range(self.max_retry_count):
            try:
                if attempt > 0:
                    print(f"重试操作 {action_type} (第{attempt + 1}次)")
                    time.sleep(1)  # 重试前等待
                
                success = self._execute_single_action(action_result)
                
                if success:
                    return True
                    
            except Exception as e:
                print(f"操作执行异常 (尝试{attempt + 1}): {e}")
                
        print(f"操作 {action_type} 在{self.max_retry_count}次尝试后仍然失败")
        return False
    
    def _execute_single_action(self, action_result: Dict[str, Any]) -> bool:
        """执行单个操作"""
        action_type = action_result.get("action_type", "")
        
        if action_type == "click":
            return self._handle_click_action(action_result)
        elif action_type == "input":
            return self._handle_input_action(action_result)
        elif action_type == "swipe":
            return self._handle_swipe_action(action_result)
        elif action_type == "scroll":
            return self._handle_scroll_action(action_result)
        elif action_type == "back":
            print("按返回键")
            return self.device_manager.press_back()
        elif action_type == "home":
            print("按Home键")
            return self.device_manager.press_home()
        elif action_type == "wait":
            wait_time = action_result.get("wait_time", 2)
            print(f"等待 {wait_time} 秒")
            time.sleep(wait_time)
            return True
        elif action_type == "complete":
            print("Agent指示测试完成")
            return True
        else:
            print(f"未知操作类型: {action_type}")
            return False
    
    def _handle_click_action(self, action_result: Dict[str, Any]) -> bool:
        """处理点击操作（ScenGen方式：检测图坐标 -> resize_ratio 映射 -> 点击）"""
        description = action_result.get("description", "")
        screenshot_path = action_result.get("screenshot_path")

        if not isinstance(screenshot_path, str) or not os.path.exists(screenshot_path):
            print("截图路径无效，无法进行检测与点击")
            return False

        # 使用本地轻量部件检测器（替代 ScenGen）
        try:
            from .detector import WidgetDetector
        except Exception as e:
            print(f"导入本地检测器失败: {e}")
            return False

        try:
            detector = WidgetDetector()
            screen_with_bbox_path, resize_ratio, elements = detector.detect(screenshot_path)
            # 记录并设置缩放比，用于设备坐标映射
            try:
                self.device_manager.resize_ratio = float(resize_ratio) if resize_ratio else 1.0
            except Exception:
                self.device_manager.resize_ratio = 1.0

            # 改进的元素匹配逻辑
            target = self._find_best_matching_element(elements, description)

            if target is None:
                print("未能匹配到目标控件，放弃点击")
                return False

            cx = (int(target["column_min"]) + int(target["column_max"])) // 2
            cy = (int(target["row_min"]) + int(target["row_max"])) // 2
            
            # 检查是否重复点击同一位置或界面无变化
            if self._is_repeat_click(cx, cy) or self._is_interface_unchanged(screenshot_path):
                print(f"检测到重复点击位置 ({cx}, {cy}) 或界面无变化，尝试智能调整...")
                # 尝试找到替代元素
                alternative_target = self._find_alternative_element(elements, description, target)
                if alternative_target:
                    cx = (int(alternative_target["column_min"]) + int(alternative_target["column_max"])) // 2
                    cy = (int(alternative_target["row_min"]) + int(alternative_target["row_max"])) // 2
                    print(f"使用替代元素，新坐标: ({cx}, {cy})")
                else:
                    # 如果没有找到替代元素，尝试微调坐标
                    cx, cy = self._adjust_coordinates(cx, cy, target)
                    print(f"微调坐标到: ({cx}, {cy})")
            
            # 记录点击坐标
            self._record_click(cx, cy)
            
            # 记录当前截图的哈希值用于界面变化检测
            self._update_screenshot_hash(screenshot_path)
            
            print(f"检测到点击中心: ({cx}, {cy}), resize_ratio={self.device_manager.resize_ratio}")
            return self.device_manager.op_click(cx, cy)
        except Exception as e:
            print(f"检测或点击过程异常: {e}")
            return False
    
    def _find_best_matching_element(self, elements: List[Dict[str, Any]], description: str) -> Optional[Dict[str, Any]]:
        """改进的元素匹配逻辑，优先匹配搜索相关元素"""
        if not elements:
            return None
            
        desc = description.lower().strip() if isinstance(description, str) else ""
        
        # 搜索相关的关键词
        search_keywords = ["搜索", "search", "放大镜", "magnify", "查找", "find"]
        
        # 第一优先级：精确文本匹配
        if desc:
            for el in elements:
                txt = (el.get("text_content") or "").lower()
                if txt and desc in txt:
                    return el
        
        # 第二优先级：搜索相关关键词匹配
        if any(keyword in desc for keyword in search_keywords):
            for el in elements:
                txt = (el.get("text_content") or "").lower()
                if txt and any(keyword in txt for keyword in search_keywords):
                    return el
        
        # 第三优先级：位置特征匹配（底部导航栏中间位置的小元素）
        if any(keyword in desc for keyword in search_keywords):
            # 筛选可能的搜索图标：小面积、位于底部区域
            candidates = []
            for el in elements:
                area = max(0, el["column_max"] - el["column_min"]) * max(0, el["row_max"] - el["row_min"])
                # 搜索图标通常面积较小（小于屏幕的1/20）且位于底部1/4区域
                if area < 50000 and el["row_min"] > 1800:  # 假设屏幕高度约2340
                    candidates.append((el, area))
            
            if candidates:
                # 选择面积适中的元素（不要太大也不太小）
                candidates.sort(key=lambda x: x[1])
                if len(candidates) >= 3:
                    return candidates[len(candidates)//2][0]  # 选择中等大小的
                else:
                    return candidates[0][0]
        
        # 最后选择：面积最大的元素（原逻辑）
        if elements:
            def _area(el: Dict[str, Any]) -> int:
                return max(0, el["column_max"] - el["column_min"]) * max(0, el["row_max"] - el["row_min"])
            return max(elements, key=_area)
        
        return None
    
    def _is_repeat_click(self, x: int, y: int) -> bool:
        """检查是否重复点击同一位置"""
        if len(self.click_history) < self.repeat_click_threshold:
            return False
        
        # 检查最近几次点击是否都在相同位置（允许5像素误差）
        tolerance = 5
        recent_clicks = self.click_history[-self.repeat_click_threshold:]
        
        for prev_x, prev_y in recent_clicks:
            if abs(x - prev_x) > tolerance or abs(y - prev_y) > tolerance:
                return False
        
        return True
    
    def _find_alternative_element(self, elements: List[Dict[str, Any]], description: str, current_target: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """寻找替代元素"""
        desc = description.lower().strip()
        search_keywords = ["搜索", "search", "放大镜", "magnify", "查找", "find", "输入", "input", "文本框", "textbox"]
        
        # 过滤掉当前目标元素
        current_bounds = (current_target["column_min"], current_target["row_min"], 
                         current_target["column_max"], current_target["row_max"])
        
        alternatives = []
        for element in elements:
            element_bounds = (element["column_min"], element["row_min"], 
                            element["column_max"], element["row_max"])
            
            # 跳过当前目标元素
            if element_bounds == current_bounds:
                continue
            
            # 计算元素面积
            area = (int(element["column_max"]) - int(element["column_min"])) * \
                   (int(element["row_max"]) - int(element["row_min"]))
            
            # 跳过过大的元素（可能是背景或容器）
            if area > 500000:  # 调整阈值
                continue
                
            # 检查是否包含搜索相关关键词
            text = element.get("text_content", "").lower()
            score = 0
            
            # 文本匹配得分
            for keyword in search_keywords:
                if keyword in text:
                    score += 10
            
            # 位置得分：优先选择屏幕上方的元素（通常搜索框在上方）
            y_center = (int(element["row_min"]) + int(element["row_max"])) // 2
            if y_center < 1000:  # 屏幕上半部分
                score += 5
            
            # 大小得分：优先选择中等大小的元素
            if 1000 < area < 50000:
                score += 3
            
            if score > 0:
                alternatives.append((score, element))
        
        # 按得分排序，返回得分最高的元素
        if alternatives:
            alternatives.sort(key=lambda x: x[0], reverse=True)
            return alternatives[0][1]
        
        return None
    
    def _adjust_coordinates(self, x: int, y: int, target: Dict[str, Any]) -> Tuple[int, int]:
        """微调坐标位置"""
        # 在元素范围内随机偏移
        width = target["column_max"] - target["column_min"]
        height = target["row_max"] - target["row_min"]
        
        # 偏移范围为元素大小的1/4
        offset_x = min(width // 4, 20)
        offset_y = min(height // 4, 20)
        
        import random
        new_x = x + random.randint(-offset_x, offset_x)
        new_y = y + random.randint(-offset_y, offset_y)
        
        # 确保坐标仍在元素范围内
        new_x = max(target["column_min"], min(new_x, target["column_max"]))
        new_y = max(target["row_min"], min(new_y, target["row_max"]))
        
        return new_x, new_y
    
    def _record_click(self, x: int, y: int):
        """记录点击坐标"""
        self.click_history.append((x, y))
        # 保持历史记录在限制范围内
        if len(self.click_history) > self.max_click_history:
            self.click_history.pop(0)
    
    def _is_interface_unchanged(self, screenshot_path: str) -> bool:
        """检查界面是否没有变化"""
        try:
            import hashlib
            with open(screenshot_path, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()
            
            if self.last_screenshot_hash is None:
                return False
            
            # 如果连续两次截图哈希值相同，说明界面没有变化
            return current_hash == self.last_screenshot_hash
        except Exception:
            return False
    
    def _update_screenshot_hash(self, screenshot_path: str):
        """更新截图哈希值"""
        try:
            import hashlib
            with open(screenshot_path, 'rb') as f:
                self.last_screenshot_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            pass

    def _handle_input_action(self, action_result: Dict[str, Any]) -> bool:
        """处理输入操作"""
        text = action_result.get("text", "")
        coordinates = action_result.get("coordinates", [])
        description = action_result.get("description", "")
        
        if not text:
            print("输入文本为空")
            return False
        
        # 预操作点击（聚焦输入框）
        focus_success = False
        if isinstance(coordinates, list) and len(coordinates) >= 2:
            try:
                x, y = int(coordinates[0]), int(coordinates[1])
                print(f"点击坐标聚焦输入: ({x}, {y})")
                focus_success = self.device_manager.op_click(x, y)
                time.sleep(self.device_manager.operation_delay)
            except (ValueError, IndexError):
                print("输入坐标解析失败，使用默认聚焦")
        
        if not focus_success:
            # 兜底：尝试聚焦顶部输入区域
            print("坐标无效，尝试聚焦顶部输入区域")
            self.device_manager.focus_top_input_area()
            time.sleep(self.device_manager.operation_delay)
        
        # 清除可能存在的旧文本
        self.device_manager.delete_chars(20) 
        time.sleep(0.5)
        
        # 输入文本
        print(f"输入文本: {text}")
        input_success = self.device_manager.op_input(text)
        
        return input_success
    
    def _handle_swipe_action(self, action_result: Dict[str, Any]) -> bool:
        """处理滑动操作（不再使用坐标，按方向滑动）"""
        direction = action_result.get("swipe_direction", "up")
        duration = action_result.get("duration", 500)
        print(f"方向滑动: {direction}")
        return self.device_manager.scroll_by_direction(direction, duration)
    
    def _handle_scroll_action(self, action_result: Dict[str, Any]) -> bool:
        """处理滚动操作"""
        direction = action_result.get("direction", "DOWN")
        duration = action_result.get("duration", 500)
        
        print(f"滚动: {direction}")
        return self.device_manager.scroll_by_direction(direction, duration)
    
    def _perform_final_check(self) -> Dict[str, Any]:
        """执行最终检查"""
        try:
            # 截图用于最终检查
            final_screenshot = self._take_screenshot(self.step_count + 1, "final")
            if not final_screenshot:
                return {
                    "success": False,
                    "error": "最终检查截图失败",
                    "screenshot": None,
                    "analysis": None
                }
            
            # 使用LLM进行最终检查
            check_result = self.visual_analyzer.perform_final_check(
                final_screenshot, 
                self.current_test
            )
            
            return {
                "success": check_result.get("success", False),
                "error": check_result.get("error"),
                "screenshot": final_screenshot,
                "analysis": check_result.get("analysis", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"最终检查异常: {e}",
                "screenshot": None,
                "analysis": None
            }
    
    def _save_test_report(self, test_result: Dict[str, Any]):
        try:
            reports_dir = self.config.get("reports_dir", "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            test_name = self.current_test.get("test_name", "unknown_test")
            safe_test_name = ''.join(c if c.isascii() and (c.isalnum() or c in ['_', '-']) else '_' for c in test_name)
            safe_test_name = re.sub(r'_+', '_', safe_test_name).strip('_-') or 'report'
            timestamp = int(time.time())
            report_filename = f"{safe_test_name}_report_{timestamp}.json"
            report_path = os.path.join(reports_dir, report_filename)
            
            test_result["device_info"] = self.device_manager.get_device_info()
            test_result["config"] = self.config
            test_result["timestamp"] = timestamp
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2)
            
            print(f"测试报告保存: {report_path}")
            
        except Exception as e:
            print(f"保存测试报告失败: {e}")
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        if self.device_manager:
            return self.device_manager.get_device_info()
        return None
    
    def cleanup(self):
        print("正在清理测试引擎资源...")
        self.current_test = None
        self.test_results = []
        print("测试引擎清理完成")