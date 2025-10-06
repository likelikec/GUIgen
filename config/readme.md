## 📄 配置文件 

### 1.LLM配置
配置说明

  - `test_engine`
    - `max_steps`：最大执行步骤数。
    - `step_timeout`：每步超时（秒）。
    - `screenshot_interval`：截图间隔（秒）。
    - `retry_count`：失败重试次数。
    - `screenshots_dir`：截图保存目录。
    - `reports_dir`：报告保存目录。
  - `llm`
    - `api_key`：LLM API Key。
    - `base_url`：LLM 基础 URL。
      - OpenAI 官方：`https://api.openai.com/v1`
      - DashScope 兼容：`https://dashscope.aliyuncs.com/compatible-mode/v1`
    - `model`：模型名称（如 `gpt-4o-mini` 或 `qwen3-vl-plus`）。
    - `temperature`：采样温度。
    - `max_tokens`：最大输出 token 数。
    - `timeout`：请求超时（秒）。
  - `device`
    - `default_device_id`：默认设备 ID（可空，自动选择）。
    - `connection_timeout`：连接超时（秒）。
    - `operation_delay`：操作后等待（秒）。
  - `logging`
    - `level`：日志级别（`DEBUG`/`INFO`）。
    - `file`：日志文件路径。
    - `console`：是否输出到控制台。


### 2.测试需求配置
为了支持基于LLM的场景驱动测试，测试需求以JSON文件描述。以下为字段说明：

- `test_id`：测试用例唯一标识（字符串）
- `test_name`：测试名称（字符串）
- `description`：测试说明（字符串）
- `app`：被测应用信息（对象）
  - `name`：应用名称（字符串）
  - `package`：应用包名（字符串）
  - `launch_activity`：应用启动Activity（字符串）
- `test_scenario`：测试场景（对象）
  - `objective`：测试目标（字符串）
  - `steps`：测试步骤列表（数组，逐步说明）
  - `test_data`：测试数据（对象，键值对，如联系人名称、输入文本等）
  - `expected_result`：总体预期结果（字符串）
 - `test_scenario.success_criteria`：成功判定标准（数组，列举达成条件）

示例（精简展示）：

```json
{
  "test_id": "test_001",
  "test_name": "微信发送消息测试",
  "description": "测试微信应用发送文本消息的功能",
  "app": {
    "name": "微信",
    "package": "com.tencent.mm",
    "launch_activity": ".ui.LauncherUI"
  },
  "test_scenario": {
    "objective": "向指定联系人发送一条文本消息",
    "steps": [
      "打开微信应用",
      "选择目标联系人",
      "输入测试消息内容",
      "发送消息",
      "验证消息发送成功"
    ],
    "test_data": {
      "contact_name": "测试联系人",
      "message_content": "这是一条测试消息"
    },
      "expected_result": "消息成功发送并显示在聊天界面中",
      "success_criteria": [
        "消息出现在聊天界面",
        "消息状态显示为已发送",
        "无错误提示"
      ]
  }
}
```

```