
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
            raise FileNotFoundError(f"Configuration file does not exist: {config_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration file: {e}")


def main():
    parser = argparse.ArgumentParser(description="GUIgen")
    parser.add_argument(
        "test_file", 
        help="Test requirement JSON file path"
    )
    parser.add_argument(
        "--device", 
        help="Specify device ID"
    )
    parser.add_argument(
        "--config", 
        default="config/config.json",
        help="Configuration file path"
    )
    parser.add_argument(
        "--max-steps", 
        type=int, 
        default=None,
        help="Maximum test steps"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=None,
        help="Timeout per step"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.test_file):
        print(f"Error: Test file does not exist: {args.test_file}")
        sys.exit(1)
    
    
    config = load_config(args.config)
    

    te_conf = config.get("test_engine", {})
    if not te_conf:
        print("Error: Configuration file missing test_engine section")
        sys.exit(1)
    if args.max_steps is not None:
        te_conf["max_steps"] = args.max_steps
    if args.timeout is not None:
        te_conf["step_timeout"] = args.timeout
    
    print("=" * 60)
    print("GUIgen")
    print("=" * 60)
    print(f"Test file: {args.test_file}")
    print(f"Max steps: {te_conf.get('max_steps')}")
    print("=" * 60)
    
    try:
        # Create test engine
        engine = TestEngine(config)
        
        # Initialize
        # Simplified initialization log, only output device ID when connection succeeds
        if not engine.initialize(device_id=args.device, llm_config=config.get("llm")):
            print("Test engine initialization failed")
            sys.exit(1)

        # Simplified device information output (no longer print screen size and current Activity)
        
        # Load test requirements
        if not engine.load_test_requirement(args.test_file):
            print("Failed to load test requirements")
            sys.exit(1)
        
        # Execute test
        result = engine.execute_test()
        
        # Display results
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        print(f"Test ID: {result.get('test_id', 'Unknown')}")
        print(f"Test Name: {result.get('test_name', 'Unknown')}")
        print(f"Steps Executed: {result.get('total_steps', 0)}/{result.get('max_steps', 0)}")
        print(f"Test Completed: {'Yes' if result.get('completed', False) else 'No'}")
        print(f"Test Success: {'Yes' if result.get('success', False) else 'No'}")
        
        if result.get('final_check'):
            final_check = result['final_check']
            print(f"Confidence: {final_check.get('confidence', 0):.2f}")
            print(f"Reasoning: {final_check.get('reasoning', 'None')}")
        
        if not result.get('success', False):
            error = result.get('error', 'Unknown error')
            print(f"Error: {error}")
        
        print("=" * 60)
        
        # Cleanup
        engine.cleanup()
        
        # Return appropriate exit code
        sys.exit(0 if result.get('success', False) else 1)
        
    except KeyboardInterrupt:
        print("\nUser interrupted test")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()