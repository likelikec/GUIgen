## 📄 Configuration Files

### 1. LLM Configuration
Configuration Description

  - `test_engine`
    - `max_steps`: Maximum execution steps.
    - `step_timeout`: Timeout per step (seconds).
    - `screenshot_interval`: Screenshot interval (seconds).
    - `retry_count`: Number of retries on failure.
    - `screenshots_dir`: Screenshot save directory.
    - `reports_dir`: Report save directory.
  - `llm`
    - `api_key`: LLM API Key.
    - `base_url`: LLM base URL.
      - OpenAI Official: `https://api.openai.com/v1`
      - DashScope Compatible: `https://dashscope.aliyuncs.com/compatible-mode/v1`
    - `model`: Model name (e.g., `gpt-4o-mini` or `qwen3-vl-plus`).
    - `temperature`: Sampling temperature.
    - `max_tokens`: Maximum output tokens.
    - `timeout`: Request timeout (seconds).
  - `device`
    - `default_device_id`: Default device ID (can be empty, auto-select).
    - `connection_timeout`: Connection timeout (seconds).
    - `operation_delay`: Wait time after operations (seconds).
  - `logging`
    - `level`: Log level (`DEBUG`/`INFO`).
    - `file`: Log file path.
    - `console`: Whether to output to console.


### 2. Test Requirements Configuration
To support LLM-based scenario-driven testing, test requirements are described in JSON files. Field descriptions are as follows:

- `test_id`: Unique test case identifier (string)
- `test_name`: Test name (string)
- `description`: Test description (string)
- `app`: Application under test information (object)
  - `name`: Application name (string)
  - `package`: Application package name (string)
  - `launch_activity`: Application launch Activity (string)
- `test_scenario`: Test scenario (object)
  - `objective`: Test objective (string)
  - `steps`: Test step list (array, step-by-step instructions)
  - `test_data`: Test data (object, key-value pairs, such as contact names, input text, etc.)
  - `expected_result`: Overall expected result (string)
 - `test_scenario.success_criteria`: Success criteria (array, listing achievement conditions)

Example (simplified display):

```json
{
  "test_id": "test_001",
  "test_name": "WeChat Send Message Test",
  "description": "Test WeChat application text message sending functionality",
  "app": {
    "name": "WeChat",
    "package": "com.tencent.mm",
    "launch_activity": ".ui.LauncherUI"
  },
  "test_scenario": {
    "objective": "Send a text message to a specified contact",
    "steps": [
      "Open WeChat application",
      "Select target contact",
      "Enter test message content",
      "Send message",
      "Verify message sent successfully"
    ],
    "test_data": {
      "contact_name": "Test Contact",
      "message_content": "This is a test message"
    },
      "expected_result": "Message successfully sent and displayed in chat interface",
      "success_criteria": [
        "Message appears in chat interface",
        "Message status shows as sent",
        "No error prompts"
      ]
  }
}
```

```
```