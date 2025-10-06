
import argparse
import json
import os
import sys
from core.test_engine import TestEngine


def load_config(config_path: str = "config/config.json") -> dict:
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
    except Exception as e:
        raise RuntimeError(f"加载配置文件失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="GUIgen")
    parser.add_argument(
        "test_file", 
        help="测试需求JSON文件路径"
    )
    parser.add_argument(
        "--device", 
        help="指定设备ID"
    )
    parser.add_argument(
        "--config", 
        default="config/config.json",
        help="配置文件路径"
    )
    parser.add_argument(
        "--max-steps", 
        type=int, 
        default=None,
        help="最大测试步数"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=None,
        help="每步超时时间"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.test_file):
        print(f"错误: 测试文件不存在: {args.test_file}")
        sys.exit(1)
    
    
    config = load_config(args.config)
    

    te_conf = config.get("test_engine", {})
    if not te_conf:
        print("错误: 配置文件缺少 test_engine 节点")
        sys.exit(1)
    if args.max_steps is not None:
        te_conf["max_steps"] = args.max_steps
    if args.timeout is not None:
        te_conf["step_timeout"] = args.timeout
    
    print("=" * 60)
    print("GUIgen")
    print("=" * 60)
    print(f"测试文件: {args.test_file}")
    print(f"最大步数: {te_conf.get('max_steps')}")
    print("=" * 60)
    
    try:
        # 创建测试引擎
        engine = TestEngine(config)
        
        # 初始化
        # 精简初始化日志，仅在连接成功时输出设备ID
        if not engine.initialize(device_id=args.device, llm_config=config.get("llm")):
            print("测试引擎初始化失败")
            sys.exit(1)

        # 精简设备信息输出（不再打印屏幕尺寸与当前Activity）
        
        # 加载测试需求
        if not engine.load_test_requirement(args.test_file):
            print("加载测试需求失败")
            sys.exit(1)
        
        # 执行测试
        result = engine.execute_test()
        
        # 显示结果
        print("\n" + "=" * 60)
        print("测试结果")
        print("=" * 60)
        print(f"测试ID: {result.get('test_id', '未知')}")
        print(f"测试名称: {result.get('test_name', '未知')}")
        print(f"执行步数: {result.get('total_steps', 0)}/{result.get('max_steps', 0)}")
        print(f"测试完成: {'是' if result.get('completed', False) else '否'}")
        print(f"测试成功: {'是' if result.get('success', False) else '否'}")
        
        if result.get('final_check'):
            final_check = result['final_check']
            print(f"置信度: {final_check.get('confidence', 0):.2f}")
            print(f"判断理由: {final_check.get('reasoning', '无')}")
        
        if not result.get('success', False):
            error = result.get('error', '未知错误')
            print(f"错误信息: {error}")
        
        print("=" * 60)
        
        # 清理
        engine.cleanup()
        
        # 返回适当的退出码
        sys.exit(0 if result.get('success', False) else 1)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()