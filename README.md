 # GUIgen: Intelligent Mobile Application Automation Testing Tool Based on Large Language Models

GUIgen is an innovative mobile application automation testing tool that adopts a Vision-Language Model (VLM) driven intelligent decision-making mechanism, achieving end-to-end automated testing processes from natural language test requirements to specific device operations. 
Through multimodal perception, intelligent reasoning, and precise execution closed-loop feedback mechanisms, this framework significantly improves the intelligence level and execution efficiency of mobile application testing.


## 1. Project Structure

```
GUIgen/
├── core/                    # Core modules
│   ├── llm_interface.py    # LLM interface layer
│   ├── visual_llm.py       # Visual analysis engine
│   ├── test_engine.py      # Test execution engine
│   ├── device_manager.py   # Device manager
│   ├── detector.py         # Element detector
│   └── prompts_visual.py   # Prompt engineering
├── config/                 # Configuration files
├── reports/               # Test reports
├── screenshots/           # Screenshot storage
└── main.py               # Main program entry


## 2. Key Technical Features

### 2.1 Multimodal Intelligent Decision Mechanism

The core innovation of the framework lies in the VLM-based multimodal decision mechanism, which achieves intelligent operation generation through the following steps:

1. **Visual Perception Stage**: Capture current application interface screenshots and extract visual features
2. **Context Construction Stage**: Combine test requirements, historical operations, and current state to build structured prompts
3. **Intelligent Reasoning Stage**: Use VLM for multimodal reasoning to generate next operation instructions
4. **Operation Parsing Stage**: Parse LLM output into standardized operation instructions
5. **Precise Execution Stage**: Execute specific operations through device manager

### 2.2 Request Analysis and Operation Execution Process After LLM Call

The specific process is as follows:

**Stage 1: LLM Response Parsing and Normalization**
```python
# Implemented in the _parse_action_response method of visual_llm.py
def _parse_action_response(self, response: str) -> Dict[str, Any]:
    # 1. Multi-level JSON parsing strategy
    # 2. Field normalization and compatibility processing  
    # 3. Operation type validation and fallback mechanism
    # 4. Error tolerance and intelligent repair
```

**Stage 2: Operation Instruction Validation and Optimization**
- **Semantic Validation**: Check logical consistency and executability of operation instructions
- **Context Adaptation**: Adjust operation parameters according to current application state
- **Duplicate Detection**: Identify and avoid invalid duplicate operations
- **Intelligent Fallback**: Provide alternative solutions when operations fail

**Stage 3: Precise Element Positioning and Operation Execution**
```python
# Implemented in the _handle_click_action method of test_engine.py
def _handle_click_action(self, action_result: Dict[str, Any]) -> bool:
    # 1. Lightweight UI element detection
    # 2. Intelligent element matching algorithm
    # 3. Coordinate mapping and transformation
    # 4. Operation execution and feedback
```

**Stage 4: Execution Result Evaluation and Feedback**
- **Interface Change Detection**: Detect operation effects through screenshot hash comparison
- **Operation Success Evaluation**: Multi-dimensional evaluation of operation execution results
- **Adaptive Adjustment**: Dynamically adjust subsequent strategies based on execution results

### 2.3 Intelligent Element Matching Algorithm

The framework implements multi-level element matching strategies:

1. **Exact Text Matching**: Prioritize matching UI elements containing target descriptions
2. **Semantic Keyword Matching**: Fuzzy matching based on semantic similarity
3. **Position Feature Matching**: Use UI layout patterns for position reasoning
4. **Area and Shape Constraints**: Combine element geometric features to improve matching accuracy

### 2.4 Adaptive Testing Strategy

- **Step-Driven Mode**: Strictly execute according to predefined test steps
- **Goal-Driven Mode**: Autonomous path planning based on test objectives
- **Hybrid Decision Mode**: Hybrid strategy combining rule constraints and intelligent reasoning

## Technical Implementation Details

### 3.1 LLM Interface Design

The framework adopts unified LLM interface design, supporting multiple large language models:

```python
class LLMInterface:
    def chat_completion(self, messages, model=None, temperature=None, max_tokens=None):
        # Unified API calling interface
        # Support for new and old OpenAI SDK compatibility
        # Error handling and retry mechanism
        
    def get_action_decision(self, screenshot_path, prompt_text, system_prompt=None):
        # Interface specifically for operation decisions
        # Integrated image encoding and multimodal processing
```

### 3.2 Prompt Engineering Strategy

The framework implements structured prompt engineering methods:

- **Layered Prompt Design**: System prompt + Task prompt + Context prompt
- **Dynamic Prompt Generation**: Dynamically build according to test scenarios and current state
- **Multi-turn Dialogue Management**: Support refinement queries and iterative optimization

### 3.3 Device Operation Abstraction

Device manager provides high-level operation abstractions:

```python
class DeviceManager:
    def op_click(self, x, y):          # Intelligent click operation
    def op_input(self, text):          # Multi-language text input
    def op_scroll(self, x1, y1, x2, y2): # Directional scroll operation
    def take_screenshot(self, save_path): # Screenshot capture
```

## Experimental Validation and Performance Analysis

### 4.1 Test Scenario Coverage

The framework has been validated on multiple mainstream mobile applications:
- QQ Music search function testing
- Ctrip flight booking process testing
- Various UI interaction mode validation

### 4.2 Performance Metrics

- **Operation Success Rate**: Significantly improve operation accuracy through intelligent matching algorithms
- **Test Efficiency**: Improve execution efficiency compared to traditional script-based testing
- **Adaptability**: Good robustness to UI changes

## Configuration and Deployment

### 5.1 Environment Requirements

- Python 3.8+
- Android Debug Bridge (ADB)
- Large language model API supporting VLM (such as Qwen-VL, GPT-4V, etc.)

### 5.2 Configuration File Structure

```json
{
  "test_engine": {
    "max_steps": 10,
    "step_timeout": 30,
    "retry_count": 3
  },
  "llm": {
    "api_key": "your_api_key_here",
    "base_url": "https://api.example.com/v1",
    "model": "qwen-vl-plus",
    "temperature": 0.1
  },
  "device": {
    "default_device_id": "device_id",
    "operation_delay": 1
  }
}
```

### 5.3 Test Requirement Definition

```json
{
  "test_id": "example_test_001",
  "test_name": "Application Function Test",
  "app": {
    "package": "com.example.app",
    "launch_activity": ".MainActivity"
  },
  "test_scenario": {
    "objective": "Test objective description",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "expected_result": "Expected result description"
  }
}
```

## Usage

### Basic Usage

```bash
python main.py config/test_requirements.json --device your_device_id
```

### Advanced Parameters

```bash
python main.py test_file.json \
  --device device_id \
  --config custom_config.json \
  --max-steps 15 \
  --timeout 60
```



## Future Development Directions

- **Multi-device Parallel Testing**: Support multiple devices executing test tasks simultaneously
- **Cross-platform Extension**: Extend to iOS and Web application testing
- **Automatic Test Case Generation**: Automatically generate test scenarios based on application analysis
- **Performance Optimization**: Further improve LLM calling efficiency and operation accuracy


```
