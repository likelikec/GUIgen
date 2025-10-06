
import base64
import json
import os
from typing import Any, Dict, List, Optional, Union

# 兼容新旧 OpenAI SDK 导入
try:
    from openai import OpenAI  # 新版 SDK
    _NEW_OPENAI_SDK = True
except Exception:
    import openai as _openai_legacy  # 旧版 SDK
    OpenAI = None
    _NEW_OPENAI_SDK = False


class LLMInterface:
    """LLM接口类，处理与OpenAI API的交互"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        初始化LLM接口
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（可选，用于自定义端点）
            model: 默认模型名称（可选）
            temperature: 默认温度参数（可选）
            max_tokens: 默认最大token数（可选）
        """
        # 强制要求使用配置文件提供的API密钥，移除环境变量默认行为
        if not api_key:
            raise ValueError("缺少LLM api_key，请在config.json的llm中配置")
        if _NEW_OPENAI_SDK:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            # 旧版SDK使用全局配置
            _openai_legacy.api_key = api_key
            if base_url:
                # 阿里通义兼容模式的base_url
                _openai_legacy.base_url = base_url
            self.client = _openai_legacy

        # 仅在提供时保存默认参数，不再内置库默认值
        self.default_model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.default_timeout = timeout
    
    def encode_image(self, image_path: str) -> str:
        """
        将图片编码为base64字符串
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            base64编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def build_content(self, message: Union[str, Dict[str, Any]]) -> Union[str, List[Dict[str, Any]]]:
        """
        构建消息内容，支持文本和图片
        
        Args:
            message: 文本消息或包含text和image字段的字典
            
        Returns:
            格式化的消息内容
        """
        if isinstance(message, str):
            return message
        
        if isinstance(message, dict):
            image = message.get("image")
            text = message.get("text")

            # 允许纯文本或纯图片消息；同时存在则为图文消息
            if image is None and text is None:
                raise ValueError("消息字典必须至少包含'text'或'image'字段")

            user_content: List[Dict[str, Any]] = []

            if text is not None:
                user_content.append({"type": "text", "text": text or ""})

            if image is not None:
                if isinstance(image, str):
                    image = [image]
                for image_path in image:
                    if os.path.exists(image_path):
                        base64_image = self.encode_image(image_path)
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        })
                    else:
                        raise FileNotFoundError(f"图片文件不存在: {image_path}")

            return user_content
        
        raise TypeError(f"不支持的消息类型: {type(message)}")
    
    def build_messages(
        self,
        user_messages: List[Union[str, Dict[str, Any]]],
        system_message: Optional[str] = None,
        assistant_messages: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        构建完整的对话消息列表
        
        Args:
            user_messages: 用户消息列表
            system_message: 系统消息（可选）
            assistant_messages: 助手消息列表（可选）
            
        Returns:
            格式化的消息列表
        """
        messages = []
        
        if system_message is not None:
            messages.append({"role": "system", "content": system_message})
        
        if assistant_messages is None and len(user_messages) == 1:
            user_content = self.build_content(user_messages[0])
            messages.append({"role": "user", "content": user_content})
        elif assistant_messages is not None and len(user_messages) == len(assistant_messages) + 1:
            for i in range(len(assistant_messages)):
                user_content = self.build_content(user_messages[i])
                messages.append({"role": "user", "content": user_content})
                messages.append({"role": "assistant", "content": assistant_messages[i]})
            user_content = self.build_content(user_messages[-1])
            messages.append({"role": "user", "content": user_content})
        else:
            raise RuntimeError("用户消息和助手消息数量不匹配")
        
        return messages
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        调用OpenAI Chat Completion API
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            包含响应内容和token使用信息的字典
        """
        try:
            # 严格使用提供或配置的模型，不再退回内置默认
            use_model = model if model is not None else self.default_model
            if not use_model:
                raise RuntimeError("LLM模型未配置，请在config.json的llm.model中设置")

            params: Dict[str, Any] = {
                "model": use_model,
                "messages": messages,
            }
            if temperature is not None:
                params["temperature"] = temperature
            elif self.default_temperature is not None:
                params["temperature"] = self.default_temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            elif self.default_max_tokens is not None:
                params["max_tokens"] = self.default_max_tokens

            # 选择超时值（优先使用调用传入，其次使用默认配置）
            use_timeout = timeout if timeout is not None else self.default_timeout

            if _NEW_OPENAI_SDK:
                if use_timeout is not None:
                    response = self.client.chat.completions.create(**params, timeout=use_timeout)
                else:
                    response = self.client.chat.completions.create(**params)
                return {
                    "content": response.choices[0].message.content,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            else:
                # 旧版 SDK 使用 request_timeout 参数
                if use_timeout is not None:
                    response = self.client.ChatCompletion.create(**params, request_timeout=use_timeout)
                else:
                    response = self.client.ChatCompletion.create(**params)
                return {
                    "content": response["choices"][0]["message"]["content"],
                    "prompt_tokens": response.get("usage", {}).get("prompt_tokens"),
                    "completion_tokens": response.get("usage", {}).get("completion_tokens"),
                    "total_tokens": response.get("usage", {}).get("total_tokens"),
                }
        except Exception as e:
            raise RuntimeError(f"LLM API调用失败: {str(e)}")
    
    def get_action_decision(
        self,
        screenshot_path: str,
        prompt_text: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        获取下一步操作决策（纯客户端模式）
        
        Args:
            screenshot_path: 当前屏幕截图路径
            prompt_text: 已构建好的用户提示词文本（来自 prompts_visual）
            system_prompt: 系统提示词（可选，如不提供则不注入默认值）
            
        Returns:
            LLM原始文本响应
        """
        user_message = {
            "image": screenshot_path,
            "text": prompt_text if prompt_text is not None else ""
        }
        messages = self.build_messages([user_message], system_prompt)
        result = self.chat_completion(messages)
        return result["content"]
    
    def check_test_completion(
        self,
        screenshot_path: str,
        prompt_text: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        检查测试是否完成（纯客户端模式）
        
        Args:
            screenshot_path: 当前屏幕截图路径
            prompt_text: 已构建好的完成检查提示词文本（来自 prompts_visual）
            system_prompt: 系统提示词（可选，如不提供则不注入默认值）
            
        Returns:
            LLM原始文本响应
        """
        user_message = {
            "image": screenshot_path,
            "text": prompt_text if prompt_text is not None else ""
        }
        messages = self.build_messages([user_message], system_prompt)
        result = self.chat_completion(messages)
        return result["content"]


class ChatContext:
    """对话上下文管理类"""
    
    def __init__(self):
        self.user_messages: List[Union[str, Dict[str, Any]]] = []
        self.assistant_messages: List[str] = []
        self.system_message: Optional[str] = None
    
    def add_user_message(self, message: Union[str, Dict[str, Any]]):
        """添加用户消息"""
        self.user_messages.append(message)
    
    def add_assistant_message(self, message: str):
        """添加助手消息"""
        self.assistant_messages.append(message)
    
    def set_system_message(self, message: str):
        """设置系统消息"""
        self.system_message = message
    
    def clear(self):
        """清空上下文"""
        self.user_messages.clear()
        self.assistant_messages.clear()
        self.system_message = None
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取格式化的消息列表"""
        llm = LLMInterface()
        return llm.build_messages(
            self.user_messages,
            self.system_message,
            self.assistant_messages
        )