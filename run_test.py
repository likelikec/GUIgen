
import os
import sys
import json
from core.test_engine import TestEngine


def run_simple_test(test_file_path: str):
    
    print("=" * 50)
    print("GUIgen")
    print("=" * 50)
    
    if not os.path.exists(test_file_path):
        print(f"错误: 测试文件不存在: {test_file_path}")
        return False
    
    try:
        # 读取配置（包含 llm 与 device 配置）
        config_path = os.path.join("config", "config.json")
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"警告: 加载配置文件失败: {e}，将使用默认配置")
        else:
            print("提示: 未找到 config/config.json，将使用默认配置")

        # 创建测试引擎（合并默认配置与外部配置）
        engine = TestEngine(config)
        
        # 初始化
        default_device_id = None
        if isinstance(config.get("device"), dict):
            default_device_id = config["device"].get("default_device_id")

        if not engine.initialize(device_id=default_device_id, llm_config=config.get("llm")):
            print("初始化失败")
            return False
        
        # 加载测试
        print(f"加载测试: {test_file_path}")
        if not engine.load_test_requirement(test_file_path):
            print("加载测试失败")
            return False
        
        # 执行测试
        result = engine.execute_test()
        
        # 显示结果
        print("\n" + "=" * 50)
        print("测试结果:")
        print(f"  成功: {'是' if result.get('success') else '否'}")
        print(f"  步数: {result.get('total_steps', 0)}")
        
        if not result.get('success'):
            print(f"  错误: {result.get('error', '未知')}")
        
        print("=" * 50)
        
        # 清理
        engine.cleanup()
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"测试异常: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python run_test.py <测试文件路径>")
        print("示例:")
        print("  python run_test.py examples/test_calculator.json")
        print("  python run_test.py config/test_requirements.json")
        sys.exit(1)
    
    test_file = sys.argv[1]
    success = run_simple_test(test_file)
    sys.exit(0 if success else 1)