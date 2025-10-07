 # GUIgen: Intelligent Mobile Application Automation Testing Tool Based on Large Language Models

GUIgen is an innovative mobile application automation testing tool that adopts a Vision-Language Model (VLM) driven intelligent decision-making mechanism, achieving end-to-end automated testing processes from natural language test requirements to specific device operations. 
Through multimodal perception, intelligent reasoning, and precise execution closed-loop feedback mechanisms, this framework significantly improves the intelligence level and execution efficiency of mobile application testing.

## 1. System Architecture Overview

GUIgen adopts a layered modular architecture design, mainly including the following core components:

- **LLM Interface Layer** (`core/llm_interface.py`): Provides unified large language model calling interface, supporting OpenAI compatible protocols
- **Visual Analysis Engine** (`core/visual_llm.py`): VLM-based screenshot analysis and operation decision module
- **Device Manager** (`core/device_manager.py`): Android device connection, control and status management
- **Test Execution Engine** (`core/test_engine.py`): Test process orchestration and execution control
- **Element Detector** (`core/detector.py`): UI element recognition and positioning algorithm
- **Prompt Engineering** (`core/prompts_visual.py`): Structured prompt templates and construction strategies

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

## Technical Contributions and Innovation Points

1. **Multimodal Test Decision**: First application of VLM to mobile application automation testing field
2. **Intelligent Operation Parsing**: Innovative LLM response parsing and operation execution mechanism
3. **Adaptive Element Matching**: Multi-level UI element intelligent matching algorithm
4. **End-to-End Automation**: Complete closed loop from natural language requirements to device operations

## Future Development Directions

- **Multi-device Parallel Testing**: Support multiple devices executing test tasks simultaneously
- **Cross-platform Extension**: Extend to iOS and Web application testing
- **Automatic Test Case Generation**: Automatically generate test scenarios based on application analysis
- **Performance Optimization**: Further improve LLM calling efficiency and operation accuracy

## Project Structure

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
```

---

*The GUIgen framework represents the technological frontier in the field of mobile application automation testing. By deeply integrating large language models with traditional testing technologies, it provides a brand new solution for intelligent testing.*

## Project Overview

GUIgen is an intelligent mobile application automation testing framework based on Large Language Models (LLM), specifically designed for Android application GUI automation testing. This framework combines computer vision, natural language processing, and mobile device control technologies to understand test requirements and automatically execute complex mobile application test scenarios.

### Core Features

- **Intelligent Test Planning**: Automatic test step generation and execution based on LLM
- **Visual Understanding**: Understand application interface state through screenshot analysis
- **Adaptive Operations**: Intelligent retry mechanisms and alternative element finding
- **Multimodal Interaction**: Support for various operation types including click, input, swipe
- **Real-time Monitoring**: Complete test process recording and report generation

## Project Structure

```
GUIgen/
├── main.py                 # Main entry file
├── requirements.txt        # Python dependencies
├── config/                 # Configuration file directory
│   ├── config.json        # Main configuration file
│   └── test_*.json        # Test case configurations
├── core/                  # Core module directory
│   ├── test_engine.py     # Test engine (core controller)
│   ├── device_manager.py  # Device manager
│   ├── llm_interface.py   # LLM interface wrapper
│   ├── visual_llm.py      # Visual analyzer
│   ├── detector.py        # UI element detector
│   ├── element.py         # Element data structure
│   └── prompts_visual.py  # Prompt templates
├── data/                  # Data directory
├── screenshots/           # Screenshot storage
├── reports/              # Test reports
├── temp/                 # Temporary files
└── static_tests/         # Static test cases
```

## Core Module Details

### 1. TestEngine (test_engine.py)
**Function**: The test engine is the core controller of the entire framework, responsible for coordinating various modules to complete test tasks.

**Main Responsibilities**:
- Test process control and step management
- Device initialization and application startup
- Screenshot collection and status monitoring
- Operation execution and retry mechanisms
- Test report generation and saving

**Core Methods**:
- `execute_test()`: Execute complete test process
- `_execute_test_steps()`: Execute specific test steps
- `_execute_action_with_retry()`: Operation execution with retry
- `_handle_click_action()`: Handle click operations
- `_find_best_matching_element()`: Intelligent element matching

**Intelligent Retry Mechanism**:
- Duplicate click detection: Monitor consecutive clicks on the same position
- Interface change detection: Determine if interface has changed through screenshot hash values
- Alternative element finding: Automatically find alternative elements when main target fails
- Coordinate fine-tuning: Make fine adjustments to click coordinates to improve success rate

### 2. DeviceManager (device_manager.py)
**Function**: Android device management and operation executor.

**Main Responsibilities**:
- ADB device connection and management
- Screen screenshot collection
- Touch operation execution (click, swipe, input)
- Application startup and control
- Device status monitoring

**Core Methods**:
- `launch_app()`: Launch specified application
- `take_screenshot()`: Take screen screenshot
- `op_click()`: Execute click operation
- `op_input()`: Execute text input
- `op_scroll()`: Execute swipe operation

**Input Processing Mechanism**:
- Support Chinese input (pinyin conversion)
- Character-by-character input mode
- ADB keyboard input
- Special character handling

### 3. VisualLLMAnalyzer (visual_llm.py)
**Function**: Vision-based LLM analyzer, responsible for understanding interfaces and generating operation instructions.

**Main Responsibilities**:
- Screenshot analysis and understanding
- Operation instruction generation
- Test completion checking
- Operation history recording
- Test report generation

**Core Methods**:
- `analyze_screenshot_for_action()`: Analyze screenshots to generate operations
- `check_test_completion()`: Check test completion status
- `_parse_action_response()`: Parse LLM responses
- `_parse_completion_response()`: Parse completion check responses

**Two-stage Analysis Mechanism**:
1. **Coarse Positioning Stage**: Generate preliminary operation instructions based on test requirements and current state
2. **Refinement Stage**: Optimize target descriptions to improve operation accuracy

### 4. LLMInterface (llm_interface.py)
**Function**: LLM API interface wrapper, supporting OpenAI-compatible APIs.

**Main Responsibilities**:
- API connection management
- Image encoding processing
- Message format construction
- Response parsing processing
- Error handling and retry

**Core Methods**:
- `encode_image()`: Image base64 encoding
- `build_content()`: Build multimodal message content
- `chat_completion()`: Execute chat completion request
- `get_action_decision()`: Get operation decisions

**Multimodal Support**:
- Text + image mixed input
- Multi-turn dialogue context management
- Flexible message format construction

### 5. WidgetDetector (detector.py)
**Function**: Lightweight UI element detector based on UIAutomator dump.

**Main Responsibilities**:
- UI hierarchy structure parsing
- Element bounding box extraction
- Text content recognition
- Element attribute mapping

**Core Methods**:
- `detect()`: Execute element detection
- `_parse_ui_dump()`: Parse UI dump XML
- `_parse_bounds()`: Parse element boundaries

### 6. Element (element.py)
**Function**: Element data structure definition.

**Data Structures**:
- `ElementRect`: Rectangle boundary definition
- `Element`: Generic element object

**Creation Methods**:
- `from_pixel_bbox()`: Create from pixel bounding box
- `from_point()`: Create from coordinate point

### 7. PromptsVisual (prompts_visual.py)
**Function**: LLM prompt template management.

**Template Types**:
- Step-based scenario prompts
- Step-free scenario prompts
- Completion check prompts
- System prompts

## Complete Workflow

### 1. Initialization Stage
```
main.py → Load configuration → Initialize TestEngine → Connect device → Initialize LLM
```

### 2. Test Execution Stage
```
Load test requirements → Launch application → Enter test loop
```

### 3. Test Loop (Each Step)
```
Screenshot collection → Visual analysis → Operation generation → Operation execution → Result recording → Status check
```

### 4. Detailed LLM Call Processing Flow

#### 4.1 Operation Analysis Flow
```
1. Screenshot encoding (base64)
2. Build prompts
   - With steps: Strict execution based on predefined steps
   - Without steps: Autonomous planning based on objectives
3. First stage LLM call (coarse positioning)
   - Send: Screenshot + test requirements + operation history
   - Receive: Preliminary operation instructions
4. Second stage LLM call (refinement, click operations only)
   - Send: Previous round results + refinement request
   - Receive: Optimized operation description
5. Response parsing and validation
6. Operation instruction return
```

#### 4.2 Completion Check Flow
```
1. Screenshot encoding
2. Build completion check prompts
3. LLM call
   - Send: Screenshot + test objectives + expected results
   - Receive: Completion status judgment
4. Response parsing
5. Return completion status
```

### 5. Operation Execution Flow

#### 5.1 Click Operation
```
1. Element detection (UIAutomator dump)
2. Element matching (based on description text)
3. Coordinate calculation (element center point)
4. Duplicate click detection
5. Intelligent retry mechanism
   - Alternative element finding
   - Coordinate fine-tuning
   - Interface change detection
6. Execute click
7. Result recording
```

#### 5.2 Input Operation
```
1. Text preprocessing
2. Input method selection
   - Character-by-character input
   - ADB keyboard input
   - Pinyin input (Chinese)
3. Execute input
4. Result validation
```

#### 5.3 Swipe Operation
```
1. Direction parsing
2. Coordinate calculation
3. Execute swipe
4. Result recording
```

### 6. Test Completion Stage
```
Final check → Report generation → Resource cleanup → Result return
```

## Configuration Instructions

### Main Configuration File (config/config.json)
```json
{
  "test_engine": {
    "max_steps": 20,
    "step_timeout": 30,
    "screenshot_interval": 2,
    "retry_count": 3,
    "screenshots_dir": "screenshots",
    "reports_dir": "reports"
  },
  "llm": {
    "api_key": "your_api_key_here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4-vision-preview",
    "temperature": 0.1,
    "max_tokens": 1000,
    "timeout": 30
  },
  "device": {
    "default_id": null,
    "connection_timeout": 30,
    "operation_delay": 1.0
  },
  "logging": {
    "level": "INFO",
    "file": "test.log",
    "console": true
  }
}
```

### Test Case Configuration (config/test_*.json)
```json
{
  "test_name": "QQ Music Search Test",
  "test_scenario": {
    "objective": "Search for specified songs in QQ Music",
    "description": "Test QQ Music search functionality",
    "search_keyword": "I Love You China",
    "expected_result": "Able to find and display related songs",
    "steps": [
      "Click search button",
      "Enter search keywords",
      "Confirm search results"
    ],
    "test_data": {
      "search_text": "I Love You China"
    }
  },
  "app": {
    "package": "com.tencent.qqmusic",
    "launch_activity": "com.tencent.qqmusic.activity.AppStarterActivity",
    "name": "QQ Music"
  }
}
```

## Usage Instructions

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure ADB is available
adb devices

# Connect Android device and enable USB debugging
```

### 2. Configuration Setup
```bash
# Edit configuration file
vim config/config.json

# Set LLM API key and endpoint
# Configure device parameters
# Adjust test parameters
```

### 3. Run Tests
```bash
# Basic usage
python main.py config/test_example.json

# Specify device
python main.py config/test_example.json --device DEVICE_ID

# Set maximum steps
python main.py config/test_example.json --max_steps 15

# Set timeout
python main.py config/test_example.json --timeout 60
```

### 4. View Results
```bash
# Test reports are located in reports/ directory
# Screenshot files are located in screenshots/ directory
# Log files are generated according to configuration
```

## Intelligent Features

### 1. Adaptive Retry Mechanism
- **Duplicate Click Detection**: Avoid ineffective repeated operations
- **Interface Change Monitoring**: Ensure operations produce expected effects
- **Alternative Element Finding**: Automatically find backup options when main target is unavailable
- **Coordinate Optimization**: Fine-tune click positions to improve success rate

### 2. Intelligent Element Matching
- **Text Similarity Calculation**: Scoring based on keyword matching degree
- **Position Priority**: Prioritize elements in the upper part of the screen
- **Size Filtering**: Exclude oversized or undersized invalid elements
- **Comprehensive Scoring System**: Multi-dimensional evaluation of best matching elements

### 3. Multimodal Understanding
- **Visual + Text**: Combine screenshots and text descriptions to understand interfaces
- **Context Awareness**: Make intelligent decisions based on operation history
- **Two-stage Analysis**: Coarse positioning + refinement to improve operation accuracy

## Extension Development

### 1. Adding New Operation Types
Add new action_type handling logic in `TestEngine._execute_single_action()`.

### 2. Custom Element Detector
Implement the `WidgetDetector` interface in `detector.py` to provide custom element detection logic.

### 3. Extend LLM Prompts
Add new prompt templates in `prompts_visual.py` to support more test scenarios.

### 4. Integrate Other LLM Services
Modify `llm_interface.py` to support other LLM API providers.

## Troubleshooting

### Common Issues
1. **Device Connection Failure**: Check ADB connection and USB debugging settings
2. **Application Launch Failure**: Confirm package name and Activity name are correct
3. **LLM Call Failure**: Check API key and network connection
4. **Element Location Failure**: Check UIAutomator service status

### Debugging Tips
1. View detailed log output
2. Check screenshot files to confirm interface status
3. Verify test configuration file format
4. Use static tests to verify basic functionality

## Contributing Guidelines

Welcome to submit Issues and Pull Requests to improve the project. Please ensure:
1. Code follows project standards
2. Add appropriate test cases
3. Update relevant documentation
4. Follow existing architectural design
