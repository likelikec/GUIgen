import argparse
import json
import os
from pathlib import Path
import sys


def ensure_repo_on_path():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def load_config(config_path: str = "config/config.json") -> dict:
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception:
        return {}


def load_scenario(scenario_dir: Path) -> dict:
    scenario_path = scenario_dir / "scenario.json"
    if not scenario_path.exists():
        raise FileNotFoundError(f"未找到场景文件: {scenario_path}")
    with scenario_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_test_requirement(scenario: dict) -> dict:
    return {
        "test_id": scenario.get("test_id", "static_case"),
        "test_name": scenario.get("test_name", "Static Visual Test"),
        "description": scenario.get("description", "静态截图操作预测与完成度检查"),
        "app": scenario.get("app", {"name": "Unknown", "platform": "android"}),
        "test_scenario": scenario.get("test_scenario", {})
    }


def find_step_images(steps_dir: Path):
    """仅收集纯数字命名的步骤图片（01.png、02.jpg 等），严格按数字排序。"""
    if not steps_dir.exists():
        return []
    import re
    pattern = re.compile(r"^(\d{2,})\.(png|jpg|jpeg)$", re.IGNORECASE)

    numbered_files = []
    for p in steps_dir.iterdir():
        if not p.is_file():
            continue
        m = pattern.match(p.name)
        if not m:
            continue
        num = int(m.group(1))
        numbered_files.append((num, p))

    numbered_files.sort(key=lambda t: t[0])
    return [p for _, p in numbered_files]


def write_report(report_path: Path, scenario: dict, predictions: list, completion: dict, missing_images: list):
    lines = []
    lines.append(f"# 静态测试报告: {scenario.get('test_name', '')}\n")
    lines.append(f"- 测试目标: {scenario.get('test_scenario', {}).get('objective', '')}\n")
    lines.append(f"- 预期结果: {scenario.get('test_scenario', {}).get('expected_result', '')}\n")
    lines.append("\n## 分步操作预测\n")
    lines.append("注：新版本LLM仅提供操作描述，具体坐标由本地检测器自动处理。\n\n")

    if not predictions:
        lines.append("- 未找到截图，请将图片放入 steps/ 目录并重试。\n")
    else:
        for i, pred in enumerate(predictions, 1):
            lines.append(f"- 步骤{i}: {pred.get('description', '无描述')}\n")
            lines.append(f"  - action_type: {pred.get('action_type', 'unknown')}\n")
            # 新逻辑不再返回坐标，由本地检测器处理
            txt = pred.get('text')
            if txt:
                lines.append(f"  - text: {txt}\n")
            lines.append(f"  - reasoning: {pred.get('reasoning', '')}\n")
            lines.append(f"  - success: {pred.get('success', True)}\n")
    
    if missing_images:
        lines.append("\n## 缺失的截图\n")
        for name in missing_images:
            lines.append(f"- {name}\n")

    lines.append("\n## 完成度检查\n")
    if completion:
        lines.append(f"- completed: {completion.get('completed', False)}\n")
        lines.append(f"- success: {completion.get('success', False)}\n")
        lines.append(f"- confidence: {completion.get('confidence', 0.0)}\n")
        lines.append(f"- reasoning: {completion.get('reasoning', '')}\n")
        achieved = completion.get('achieved_criteria') or []
        missing = completion.get('missing_criteria') or []
        if achieved:
            lines.append("- 已达成标准:\n")
            for c in achieved:
                lines.append(f"  - {c}\n")
        if missing:
            lines.append("- 未达成标准:\n")
            for c in missing:
                lines.append(f"  - {c}\n")
        if completion.get('next_suggestion'):
            lines.append(f"- 建议下一步: {completion['next_suggestion']}\n")
    else:
        lines.append("- 未进行完成度检查（无可用截图）。\n")

    report_path.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="静态截图操作预测与报告生成")
    parser.add_argument("--scenario", type=str, default=str(Path("static_tests/ctrip_flight_booking")), help="场景目录路径")
    parser.add_argument("--api-key", type=str, default=None, help="可选，直传 API Key（OpenAI/DashScope）")
    parser.add_argument("--base-url", type=str, default=None, help="可选，自定义 Base URL（如 DashScope 兼容模式）")
    parser.add_argument("--model", type=str, default=None, help="可选，模型名称（如 qwen3-vl-plus）")
    args = parser.parse_args()

    ensure_repo_on_path()

    # 延迟导入以确保路径已设置
    from core.llm_interface import LLMInterface
    from core.visual_llm import VisualLLMAnalyzer

    # 加载配置（支持从 config/config.json 读取默认 LLM 参数）
    config = load_config()
    llm_cfg = (config or {}).get("llm", {})

    scenario_dir = Path(args.scenario).resolve()
    scenario = load_scenario(scenario_dir)
    test_requirement = build_test_requirement(scenario)

    steps_dir = scenario_dir / "steps"
    images = find_step_images(steps_dir)

    # 解析 LLM 参数：命令行优先，其次配置文件，最后环境变量（由 LLMInterface 处理）
    api_key = args.api_key if args.api_key is not None else llm_cfg.get("api_key")
    base_url = args.base_url if args.base_url is not None else llm_cfg.get("base_url")
    model = args.model if args.model is not None else llm_cfg.get("model")

    # 准备LLM接口
    llm = LLMInterface(api_key=api_key, base_url=base_url, model=model)
    visual = VisualLLMAnalyzer(llm)

    predictions = []
    missing_images = []

    if not images:
        # 记录期望的文件名，提示用户补充（按纯数字命名）
        steps_def = test_requirement.get("test_scenario", {}).get("steps", [])
        count = len(steps_def) if steps_def else 6
        expected = [f"{i:02d}.png" for i in range(1, count + 1)]
        for name in expected:
            if not (steps_dir / name).exists():
                missing_images.append(name)
        completion = {}
    else:
        max_steps = len(images)
        for idx, img_path in enumerate(images, start=1):
            try:
                result = visual.analyze_screenshot_for_action(
                    screenshot_path=str(img_path),
                    test_requirement=test_requirement,
                    current_step=idx,
                    max_steps=max_steps,
                )
                predictions.append(result)
            except Exception as e:
                predictions.append({
                    "action_type": "unknown",
                    "description": f"分析失败: {e}",
                    "reasoning": "在静态模式下分析该截图时发生错误",
                    "success": False
                })

        try:
            completion = visual.check_test_completion(
                screenshot_path=str(images[-1]),
                test_requirement=test_requirement
            )
        except Exception as e:
            completion = {
                "completed": False,
                "success": False,
                "confidence": 0.0,
                "reasoning": f"完成度检查失败: {e}",
            }

    # 输出结果
    (scenario_dir / "predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(scenario_dir / "report.md", scenario, predictions, completion, missing_images)

    print(f"预测与报告已生成：{scenario_dir}")


if __name__ == "__main__":
    main()