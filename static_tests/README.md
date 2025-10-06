# 静态操作预测与报告

本目录基于静态截图进行“操作预测”和“完成度检查”，并生成测试报告。

## 场景目录与文件职责
- `scenario.json`：场景描述。最小字段可仅包含：
  - `app_name`：应用名称（如 `QQ音乐`）。
  - `test_scenario.objective`：测试目标（如“搜索《北京欢迎你》”）。
  - 可选字段：`expected_result`（期望结果文案）、`success_criteria`（成功判定标准列表）、`steps`（若需要硬编码步骤说明）。
- `steps/`：分步截图目录。按顺序命名（如 `01.png`, `02.png`）。脚本将按文件名顺序读取并进行操作预测。
- `predictions.json`：每张截图的操作预测结果列表。每项包含：
  - `action_type`：预测的操作类型（`click`/`input`/`swipe`/`complete`/`error` 等）。
  - `description`：操作描述或错误说明。
  - `coordinates`：点击/滑动坐标（如有）。
  - `text`：需要输入的文本（如有）。
  - `reasoning`：LLM 的判断理由。
  - `success`：该步是否合理或达成目的的标记。
- `report.md`：场景的汇总报告，包括：
  - 测试目标与预期结果（来自 `scenario.json`）。
  - 分步操作预测的摘要。
  - 完成度检查结果：`completed`、`success`、`confidence`、`reasoning`，以及已/未达成的成功标准与下一步建议。

## 置信度（confidence）说明
- 含义：`confidence` 表示完成度判断的可信程度（0–1），数值越高表示模型越确信测试已完成或未完成的判断及其理由。
- 来源：在完成度检查阶段，系统向视觉 LLM 发送结构化提示，要求返回 JSON，其中包含 `confidence` 字段。若返回为有效 JSON，则直接使用模型提供的数值；若响应非 JSON，仅基于关键词进行兜底判断，则使用默认值 `0.5`；若 JSON 解析失败，则为 `0.0`。
- 计算方式：`confidence` 由 LLM 根据当前截图与测试目标、成功标准的匹配程度自行评估与给出。代码不会二次推理计算，只进行范围与格式兜底（如默认值与解析失败的处理）。
- 典型解读：
  - `>= 0.8`：高度可信，基本可视为结论可靠。
  - `0.5–0.8`：中等可信，建议结合 `reasoning` 与已/未达成标准进一步人工确认。
  - `< 0.5`：低可信，建议复核截图或补充明确的成功标准。

## 运行方法
- 基本用法（仅指定场景目录）：
  - `python static_tests/run_static_test.py --scenario static_tests/qqmusic2`
  - LLM 参数默认从 `config/config.json` 读取（如 `api_key`、`base_url`、`model`）。
- 覆盖 LLM 参数：
  - `python static_tests/run_static_test.py --scenario static_tests/qqmusic2 --model gpt-4o-mini --base-url https://api.openai.com/v1 --api-key sk_...`
  - 参数优先级：命令行 > `config/config.json` > 环境变量。

## 示例场景结构
```
static_tests/
  qqmusic2/
    scenario.json
    steps/
      01.png
      02.png
      03.png
```

## 常见操作
- 创建新场景：复制一个现有场景目录，修改其 `scenario.json`（可最小化仅保留 `app_name` 与 `objective`），并替换 `steps/` 内的截图。
- 快速验证：仅提供 `scenario.json` 的目标与若干 `steps` 截图即可运行。若没有步骤图，报告会标注缺失并只进行完成度检查（若能获取到最后一张截图）。
- 明确成功标准：在 `success_criteria` 中列出要满足的界面元素或结果文本，可提高完成度判断的可靠性与 `confidence`。

## 注意事项
- 若暂时没有真实截图，可先创建占位图片，脚本会跳过并在报告中标注缺失。
- LLM 需具备视觉能力（支持图像 + 文本输入）。若更换到兼容模式（如 DashScope），请正确设置 `base_url`：`https://dashscope.aliyuncs.com/compatible-mode/v1`。
- 为确保稳定性，建议在 `config/config.json` 中设定默认模型与参数，并在需要时通过命令行进行临时覆盖。