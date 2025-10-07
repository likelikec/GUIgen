
import os
import sys
import json
from core.test_engine import TestEngine


def run_simple_test(test_file_path: str):
    
    print("=" * 50)
    print("GUIgen")
    print("=" * 50)
    
    if not os.path.exists(test_file_path):
        print(f"Error: Test file does not exist: {test_file_path}")
        return False
    
    try:
        # Read configuration (including llm and device configuration)
        config_path = os.path.join("config", "config.json")
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load configuration file: {e}, will use default configuration")
        else:
            print("Info: config/config.json not found, will use default configuration")

        # Create test engine (merge default configuration with external configuration)
        engine = TestEngine(config)
        
        # Initialize
        default_device_id = None
        if isinstance(config.get("device"), dict):
            default_device_id = config["device"].get("default_device_id")

        if not engine.initialize(device_id=default_device_id, llm_config=config.get("llm")):
            print("Initialization failed")
            return False
        
        # Load test
        print(f"Loading test: {test_file_path}")
        if not engine.load_test_requirement(test_file_path):
            print("Failed to load test")
            return False
        
        # Execute test
        result = engine.execute_test()
        
        # Display results
        print("\n" + "=" * 50)
        print("Test Results:")
        print(f"  Success: {'Yes' if result.get('success') else 'No'}")
        print(f"  Steps: {result.get('total_steps', 0)}")
        
        if not result.get('success'):
            print(f"  Error: {result.get('error', 'Unknown')}")
        
        print("=" * 50)
        
        # Cleanup
        engine.cleanup()
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"Test exception: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_test.py <test_file_path>")
        print("Examples:")
        print("  python run_test.py examples/test_calculator.json")
        print("  python run_test.py config/test_requirements.json")
        sys.exit(1)
    
    test_file = sys.argv[1]
    success = run_simple_test(test_file)
    sys.exit(0 if success else 1)