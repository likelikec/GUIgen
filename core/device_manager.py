
import os
import subprocess
import time
from typing import Optional, Tuple, Dict, Any, List
import json
import re
try:
    from pypinyin import lazy_pinyin  # Chinese to pinyin conversion (fallback)
except Exception:
    lazy_pinyin = None


class DeviceManager:
    """Android device management class"""
    
    def __init__(self, device_id: Optional[str] = None, device_config: Optional[Dict[str, Any]] = None):
        """
        Initialize device manager
        
        Args:
            device_id: Specified device ID, if None use the first available device
            device_config: Device-related configuration (must include operation_delay and connection_timeout)
        """
        if device_config is None:
            raise ValueError("Missing device configuration, please set in config.json device section")
        if "operation_delay" not in device_config or "connection_timeout" not in device_config:
            raise ValueError("Device configuration missing required items: operation_delay or connection_timeout")

        self.operation_delay = float(device_config.get("operation_delay"))
        self.connection_timeout = int(device_config.get("connection_timeout"))
        
        # Device properties
        self.resize_ratio = device_config.get("resize_ratio", 1.0)  # Coordinate scaling ratio
        self.rotate_angle = device_config.get("rotate_angle", 0)   # Screen rotation angle

        self.device_id = self._get_device_id(device_id)
        self.screen_size = self._get_screen_size()
        self.width, self.height = self.screen_size
        
    def _get_device_id(self, device_id: Optional[str] = None) -> str:
        """Get device ID, retry waiting for device connection according to connection_timeout"""
        start = time.time()
        while True:
            try:
                result = subprocess.run(
                    "adb devices",
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split('\n')[1:]  # Skip header line
                devices = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            device_id_found, status = parts[0], parts[1]
                            if status == 'device':  # Only consider connected devices
                                devices.append(device_id_found)
                if devices:
                    if device_id is None:
                        return devices[0]
                    elif device_id in devices:
                        return device_id
                    else:
                        raise ValueError(f"指定的设备ID不存在: {device_id}")
                if time.time() - start >= self.connection_timeout:
                    raise RuntimeError("没有找到已连接的Android设备")
                time.sleep(1)
            except subprocess.CalledProcessError as e:
                if time.time() - start >= self.connection_timeout:
                    raise RuntimeError(f"ADB命令执行失败: {e}")
                time.sleep(1)
    
    def _get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        try:
            result = subprocess.run(
                f"adb -s {self.device_id} shell wm size",
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析输出，格式通常为 "Physical size: 1080x2340"
            output = result.stdout.strip()
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split('x'))
                return width, height
            else:
                # 默认尺寸
                return 1080, 2340
                
        except (subprocess.CalledProcessError, ValueError):
            # 如果获取失败，返回默认尺寸
            return 1080, 2340
    
    def launch_app(self, package_name: str, activity_name: str) -> bool:
        """
        启动应用
        
        Args:
            package_name: 应用包名
            activity_name: 启动Activity名称
            
        Returns:
            是否启动成功
        """
        try:
            cmd = f"adb -s {self.device_id} shell am start -n {package_name}/{activity_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"应用启动成功: {package_name}")
                time.sleep(3)  # 等待应用启动
                return True
            else:
                print(f"应用启动失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"启动应用异常: {e}")
            return False
    
    def take_screenshot(self, save_path: str) -> bool:
        """
        截取屏幕截图
        
        Args:
            save_path: 保存路径
            
        Returns:
            是否截图成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 设备上的临时路径
            device_path = "/sdcard/screenshot_temp.png"
            
            # 在设备上截图
            cmd1 = f"adb -s {self.device_id} shell screencap -p {device_path}"
            result1 = subprocess.run(cmd1, shell=True, capture_output=True)
            
            if result1.returncode != 0:
                return False
            
            # 拉取到本地
            cmd2 = f"adb -s {self.device_id} pull {device_path} \"{save_path}\""
            result2 = subprocess.run(cmd2, shell=True, capture_output=True)
            
            # 清理设备上的临时文件
            cmd3 = f"adb -s {self.device_id} shell rm {device_path}"
            subprocess.run(cmd3, shell=True)
            
            return result2.returncode == 0
            
        except Exception as e:
            print(f"截图异常: {e}")
            return False
    
    def op_click(self, x: int, y: int) -> bool:
        """
        点击操作 - 支持坐标变换
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            是否点击成功
        """
        try:
            # 应用坐标变换
            transformed_x, transformed_y = self._transform_coordinates(x, y)
            
            cmd = f"adb -s {self.device_id} shell input tap {transformed_x} {transformed_y}"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)
            return result.returncode == 0
        except Exception as e:
            print(f"点击操作异常: {e}")
            return False

    # 新增：基于元素对象的点击与存在性断言
    def op_click_element(self, element: "Element", screenshot_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        点击元素中心，并进行基本存在性断言。

        Args:
            element: 元素对象（包含 rect 与 center）
            screenshot_size: 若中心坐标基于截图像素，则传入截图 (width, height) 以映射到设备坐标

        Returns:
            是否点击成功
        """
        try:
            cx, cy = element.center
            # 断言矩形有效且在屏幕范围内（像素域）
            if element.rect.width == 0 and element.rect.height == 0:
                # 点元素允许，但仍需在屏幕范围
                pass

            # 若提供了截图尺寸，则按比例映射中心点到设备坐标
            if screenshot_size is not None:
                sw, sh = screenshot_size
                if sw > 0 and sh > 0:
                    ratio_x = self.width / float(sw)
                    ratio_y = self.height / float(sh)
                    cx = int(round(cx * ratio_x))
                    cy = int(round(cy * ratio_y))

            # 屏幕范围断言
            if not (0 <= cx <= self.width and 0 <= cy <= self.height):
                print(f"元素中心超出屏幕范围: ({cx}, {cy}) / {self.width}x{self.height}")
                return False

            return self.op_click(cx, cy)
        except Exception as e:
            print(f"元素点击异常: {e}")
            return False

    def assert_element_visible(self, element: "Element") -> bool:
        """基本可见性断言：矩形尺寸非负且中心落在屏幕范围内。"""
        try:
            cx, cy = element.center
            in_bounds = 0 <= cx <= self.width and 0 <= cy <= self.height
            has_area = element.rect.width >= 0 and element.rect.height >= 0
            return in_bounds and has_area
        except Exception:
            return False
    
    def click(self, x: int, y: int) -> bool:
        """
        点击屏幕坐标 - 兼容原有接口
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            是否点击成功
        """
        return self.op_click(x, y)
    
    def op_input(self, text: str) -> bool:
        """
        输入操作 - 智能字符处理
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否输入成功
        """
        try:
            # 字符处理
            processed_text = self._process_input_text(text)

            # 尝试直接输入
            # adb 对空格有特殊处理，优先尝试整串；失败会走逐词策略
            cmd = f"adb -s {self.device_id} shell input text \"{processed_text}\""
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)

            if result.returncode == 0:
                return True
            
            # 回退策略1：逐词输入（处理空格问题）
            if self._input_word_by_word(text):
                return True

            # 回退策略2：中文转拼音后输入（未安装 ADB Keyboard 时的兜底）
            if self._input_with_pinyin(text):
                return True

            # 回退策略3：使用ADB Keyboard（处理复杂字符）
            if self._input_with_adb_keyboard(text):
                return True

            return False
            
        except Exception as e:
            print(f"输入操作异常: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """
        输入文本 - 兼容原有接口
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否输入成功
        """
        return self.op_input(text)
    
    def op_scroll(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """
        滚动操作
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滚动持续时间（毫秒）
            
        Returns:
            是否滚动成功
        """
        try:
            # 应用坐标变换
            start_x, start_y = self._transform_coordinates(x1, y1)
            end_x, end_y = self._transform_coordinates(x2, y2)
            
            cmd = f"adb -s {self.device_id} shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)
            return result.returncode == 0
        except Exception as e:
            print(f"滚动操作异常: {e}")
            return False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """
        滑动屏幕 - 兼容原有接口
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滑动持续时间（毫秒）
            
        Returns:
            是否滑动成功
        """
        return self.op_scroll(x1, y1, x2, y2, duration)
    
    def scroll_by_direction(self, direction: str, duration: int = 500) -> bool:
        """
        方向滚动
        
        Args:
            direction: 滚动方向 (UP, DOWN, LEFT, RIGHT)
            duration: 滚动持续时间（毫秒）
            
        Returns:
            是否滚动成功
        """
        try:
            w, h = self.width, self.height
            
            # 滚动参数
            scroll_args = {
                "DOWN": (w // 2, int(h * 0.8), w // 2, int(h * 0.2)),
                "UP": (w // 2, int(h * 0.2), w // 2, int(h * 0.8)),
                "RIGHT": (int(w * 0.8), h // 2, int(w * 0.2), h // 2),
                "LEFT": (int(w * 0.2), h // 2, int(w * 0.8), h // 2),
            }
            
            direction_upper = direction.upper()
            if direction_upper not in scroll_args:
                print(f"不支持的滚动方向: {direction}")
                return False
            
            x1, y1, x2, y2 = scroll_args[direction_upper]
            return self.op_scroll(x1, y1, x2, y2, duration)
            
        except Exception as e:
            print(f"方向滚动异常: {e}")
            return False
    
    def delete_chars(self, count: int = 1) -> bool:
        """
        字符删除
        
        Args:
            count: 要删除的字符数量
            
        Returns:
            是否删除成功
        """
        try:
            for _ in range(count):
                cmd = f"adb -s {self.device_id} shell input keyevent 67"  # KEYCODE_DEL
                result = subprocess.run(cmd, shell=True, capture_output=True)
                if result.returncode != 0:
                    return False
                time.sleep(0.1)  # 短暂延迟
            return True
        except Exception as e:
            print(f"删除字符异常: {e}")
            return False
    
    def back(self) -> bool:
        """返回操作"""
        return self.press_back()
    
    def wait(self, seconds: float = 1.0) -> bool:
        """等待操作"""
        try:
            time.sleep(seconds)
            return True
        except Exception:
            return False
    
    def _transform_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """
        坐标变换 - 采用 ScenGen 方式：检测图坐标按 resize_ratio 映射回设备坐标，并支持旋转。

        Args:
            x: 检测图中的X坐标（像素）
            y: 检测图中的Y坐标（像素）

        Returns:
            设备像素坐标 (x, y)
        """
        ratio = self.resize_ratio if self.resize_ratio and self.resize_ratio > 0 else 1.0
        # ScenGen：设备坐标 = 检测图坐标 / resize_ratio
        scaled_x = int(round(x / ratio))
        scaled_y = int(round(y / ratio))

        # 旋转变换
        if self.rotate_angle == 90:
            return scaled_y, self.width - scaled_x
        elif self.rotate_angle == 180:
            return self.width - scaled_x, self.height - scaled_y
        elif self.rotate_angle == 270:
            return self.height - scaled_y, scaled_x
        else:
            return scaled_x, scaled_y
    
    def _process_input_text(self, text: str) -> str:
        """
        输入文本处理
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 转义特殊字符
        processed = text.replace("\\", "\\\\")
        processed = processed.replace("\"", "\\\"")
        processed = processed.replace("'", "\\'")
        processed = processed.replace("&", "\\&")
        processed = processed.replace("|", "\\|")
        processed = processed.replace(";", "\\;")
        processed = processed.replace("(", "\\(")
        processed = processed.replace(")", "\\)")
        processed = processed.replace("<", "\\<")
        processed = processed.replace(">", "\\>")
        processed = processed.replace("$", "\\$")
        processed = processed.replace("`", "\\`")
        
        return processed
    
    def _input_word_by_word(self, text: str) -> bool:
        """
        逐词输入策略
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否输入成功
        """
        try:
            words = text.split(" ")
            for i, word in enumerate(words):
                if not word:
                    continue
                
                # 输入单词
                processed_word = self._process_input_text(word)
                cmd = f"adb -s {self.device_id} shell input text \"{processed_word}\""
                result = subprocess.run(cmd, shell=True, capture_output=True)
                
                if result.returncode != 0:
                    return False
                
                time.sleep(self.operation_delay)
                
                # 如果不是最后一个单词，添加空格
                if i < len(words) - 1:
                    space_cmd = f"adb -s {self.device_id} shell input keyevent 62"  # KEYCODE_SPACE
                    subprocess.run(space_cmd, shell=True)
                    time.sleep(self.operation_delay)
            
            return True
        except Exception as e:
            print(f"逐词输入异常: {e}")
            return False
    
    def _input_with_adb_keyboard(self, text: str) -> bool:
        """
        ADB Keyboard输入策略
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否输入成功
        """
        try:
            # 检查是否安装了ADB Keyboard
            ime_list = subprocess.run(
                f"adb -s {self.device_id} shell ime list -s",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if ime_list.returncode != 0:
                return False
            
            ime_output = ime_list.stdout
            if 'com.android.adbkeyboard/.AdbIME' not in ime_output:
                print("ADB Keyboard未安装，无法使用广播输入")
                return False
            
            # 切换到ADB Keyboard
            set_ime = subprocess.run(
                f"adb -s {self.device_id} shell ime set com.android.adbkeyboard/.AdbIME",
                shell=True,
                capture_output=True
            )
            
            if set_ime.returncode != 0:
                return False
            
            time.sleep(self.operation_delay)
            
            # 使用广播输入
            broadcast_cmd = f"adb -s {self.device_id} shell am broadcast -a ADB_INPUT_TEXT --es msg '{text}'"
            result = subprocess.run(broadcast_cmd, shell=True, capture_output=True)
            
            time.sleep(self.operation_delay)
            return result.returncode == 0
            
        except Exception as e:
            print(f"ADB Keyboard输入异常: {e}")
            return False

    def _input_with_pinyin(self, text: str) -> bool:
        """
        将中文文本转为拼音后输入，适用于未安装 ADB Keyboard 的场景。

        Args:
            text: 原始文本

        Returns:
            是否输入成功
        """
        try:
            if not text:
                return False
            # 若库不可用或文本为纯 ASCII，则跳过
            if lazy_pinyin is None:
                return False
            if all(ord(c) < 128 for c in text):
                return False

            pinyin_words = lazy_pinyin(text)
            if not pinyin_words:
                return False
            # 以空格连接，便于中文搜索框常见语义匹配
            pinyin_text = " ".join(pinyin_words)

            processed = self._process_input_text(pinyin_text)
            cmd = f"adb -s {self.device_id} shell input text \"{processed}\""
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)
            return result.returncode == 0
        except Exception as e:
            print(f"拼音输入异常: {e}")
            return False

    def get_screen_size(self) -> Optional[tuple]:
        """Get screen size (width, height)"""
        return self.screen_size

    def focus_top_input_area(self) -> bool:
        """
        聚焦顶部输入区域
        
        Returns:
            是否聚焦成功
        """
        try:
            # 点击屏幕上方区域，通常是搜索框或输入框的位置
            x = self.width // 2
            y = int(self.height * 0.15)  # 屏幕上方15%的位置
            
            return self.op_click(x, y)
        except Exception as e:
            print(f"聚焦输入区域异常: {e}")
            return False





    def press_back(self) -> bool:
        """
        按返回键
        
        Returns:
            是否操作成功
        """
        try:
            cmd = f"adb -s {self.device_id} shell input keyevent 4"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)
            return result.returncode == 0
        except Exception as e:
            print(f"返回键操作异常: {e}")
            return False

    def press_home(self) -> bool:
        """
        按Home键
        
        Returns:
            是否操作成功
        """
        try:
            cmd = f"adb -s {self.device_id} shell input keyevent 3"
            result = subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(self.operation_delay)
            return result.returncode == 0
        except Exception as e:
            print(f"Home键操作异常: {e}")
            return False

    def get_current_activity(self) -> Optional[str]:
        """
        获取当前Activity
        
        Returns:
            当前Activity名称，失败返回None
        """
        try:
            cmd = f"adb -s {self.device_id} shell dumpsys activity activities | grep mResumedActivity"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # 解析输出获取Activity名称
                output = result.stdout.strip()
                if "ActivityRecord" in output:
                    parts = output.split()
                    for part in parts:
                        if "/" in part and "." in part:
                            return part
            return None
        except Exception as e:
            print(f"获取当前Activity异常: {e}")
            return None

    def get_device_info(self) -> Dict[str, Any]:
        """
        获取设备信息
        
        Returns:
            设备信息字典
        """
        return {
            "device_id": self.device_id,
            "screen_size": self.screen_size,
            "width": self.width,
            "height": self.height,
            "current_activity": self.get_current_activity(),
            "operation_delay": self.operation_delay,
            "connection_timeout": self.connection_timeout,
            "resize_ratio": self.resize_ratio,
            "rotate_angle": self.rotate_angle,
        }