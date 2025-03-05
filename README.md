# AutoHedge 🚀

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/agora-999382051935506503) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@kyegomez3242) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kye-g-38759a207/) [![Follow on X.com](https://img.shields.io/badge/X.com-Follow-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/kyegomezb)


[![PyPI version](https://badge.fury.io/py/autohedge.svg)](https://badge.fury.io/py/autohedge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/autohedge/badge/?version=latest)](https://autohedge.readthedocs.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Build your autonomous hedge fund in minutes. AutoHedge harnesses the power of swarm intelligence and AI agents to automate market analysis, risk management, and trade execution.

## 🌟 Features

- **Multi-Agent Architecture**: Leverages specialized AI agents for different aspects of trading
  - Director Agent for strategy and thesis generation
  - Quant Agent for technical analysis
  - Risk Management Agent for position sizing and risk assessment
  - Execution Agent for trade implementation

- **Real-Time Market Analysis**: Integrates with market data providers for live analysis
- **Risk-First Approach**: Built-in risk management and position sizing
- **Structured Output**: JSON-formatted trade recommendations and analysis
- **Comprehensive Logging**: Detailed logging system for trade tracking and debugging
- **Extensible Framework**: Easy to customize and extend with new capabilities

## 📋 Requirements

- Python 3.8+
- `swarms` package
- `tickr-agent`
- Additional dependencies listed in `requirements.txt`

## 🚀 Quick Start

### Installation

```bash
pip install -U autohedge
```

### Environment Variables

```bash
OPENAI_API_KEY=""
WORKSPACE_DIR="agent_workspace"
```

### Basic Usage

```python
# Example usage
from autohedge import AutoHedge

# Define the stocks to analyze
stocks = ["NVDA"]

# Initialize the trading system with the specified stocks
trading_system = AutoHedge(stocks)

# Define the task for the trading cycle
task = "Let's analyze nvidia to see if we should buy it, we have 50k$ in allocation"

# Run the trading cycle and print the results
print(trading_system.run(task=task))

```

## 🏗️ Architecture

AutoHedge uses a multi-agent architecture where each agent specializes in a specific aspect of the trading process:

```mermaid
graph TD
    A[Director Agent] --> B[Quant Agent]
    B --> C[Risk Manager]
    C --> D[Execution Agent]
    D --> E[Trade Output]
```

### Agent Roles

1. **Director Agent**
   - Generates trading theses
   - Coordinates overall strategy
   - Analyzes market conditions

2. **Quant Agent**
   - Performs technical analysis
   - Evaluates statistical patterns
   - Calculates probability scores

3. **Risk Manager**
   - Assesses trade risks
   - Determines position sizing
   - Sets risk parameters

4. **Execution Agent**
   - Generates trade orders
   - Sets entry/exit points
   - Manages order execution

## 📊 Output Format

AutoHedge generates structured output using Pydantic models:

```python
class AutoHedgeOutput(BaseModel):
    id: str                         # Unique identifier
    name: Optional[str]             # Strategy name
    description: Optional[str]      # Strategy description
    stocks: Optional[List[str]]     # List of stocks
    task: Optional[str]             # Analysis task
    thesis: Optional[str]           # Trading thesis
    risk_assessment: Optional[str]  # Risk analysis
    order: Optional[Dict]           # Trade order details
    timestamp: str                  # Timestamp
    current_stock: str              # Current stock being analyzed
```

## 🔧 Configuration

AutoHedge can be configured through environment variables or initialization parameters:

```python
trading_system = AutoHedge(
    name="CustomStrategy",
    description="My Trading Strategy",
    stocks=["NVDA", "AAPL"],
    output_dir="custom_outputs"
)
```


## 📝 Logging

AutoHedge uses the `loguru` library for comprehensive logging:

```python
logger.add(
    "trading_system_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
)
```

## 🔍 Advanced Usage

### Custom Agent Configuration

```python
from autohedge import TradingDirector, QuantAnalyst, RiskManager

# Custom director configuration
director = TradingDirector(
    stocks=["NVDA", "AAPL"],
    output_dir="custom_outputs"
)

# Custom analysis
analysis = director.generate_thesis(
    task="Generate comprehensive analysis",
    stock="NVDA"
)
```

### Risk Management

```python
from autohedge import RiskManager

risk_manager = RiskManager()
assessment = risk_manager.assess_risk(
    stock="NVDA",
    thesis=thesis,
    quant_analysis=analysis
)
```

# Diagrams

## 🏗️ System Architecture

### High-Level Component Overview
```mermaid
flowchart TB
    subgraph Client
        A[AutoHedge Client] --> B[Trading System]
    end
    
    subgraph Agents["Multi-Agent System"]
        B --> C{Director Agent}
        C --> D[Quant Agent]
        C --> E[Risk Agent]
        C --> F[Execution Agent]
        
        D --> G[Technical Analysis]
        D --> H[Statistical Analysis]
        
        E --> I[Risk Assessment]
        E --> J[Position Sizing]
        
        F --> K[Order Generation]
        F --> L[Trade Execution]
    end
    
    subgraph Output
        K --> M[JSON Output]
        L --> N[Trade Logs]
    end
```

### Trading Cycle Sequence
```mermaid
sequenceDiagram
    participant C as Client
    participant D as Director
    participant Q as Quant
    participant R as Risk
    participant E as Execution
    
    C->>D: Initialize Trading Cycle
    activate D
    D->>D: Generate Thesis
    D->>Q: Request Analysis
    activate Q
    Q-->>D: Return Analysis
    deactivate Q
    D->>R: Request Risk Assessment
    activate R
    R-->>D: Return Risk Profile
    deactivate R
    D->>E: Generate Order
    activate E
    E-->>D: Return Order Details
    deactivate E
    D-->>C: Return Complete Analysis
    deactivate D
```

### Trade State Machine
```mermaid
stateDiagram-v2
    [*] --> Initialization
    Initialization --> ThesisGeneration
    
    ThesisGeneration --> QuantAnalysis
    QuantAnalysis --> RiskAssessment
    
    RiskAssessment --> OrderGeneration: Risk Approved
    RiskAssessment --> ThesisGeneration: Risk Rejected
    
    OrderGeneration --> OrderExecution
    OrderExecution --> Monitoring
    
    Monitoring --> ThesisGeneration: New Cycle
    Monitoring --> [*]: Complete
```

### Data Flow
```mermaid
flowchart LR
    subgraph Input
        A[Market Data] --> B[Technical Indicators]
        A --> C[Fundamental Data]
    end
    
    subgraph Processing
        B --> D[Quant Analysis]
        C --> D
        D --> E[Risk Analysis]
        E --> F[Order Generation]
    end
    
    subgraph Output
        F --> G[Trade Orders]
        F --> H[Risk Reports]
        F --> I[Performance Metrics]
    end
```

### Class Structure
```mermaid
classDiagram
    class AutoHedge {
        +String name
        +String description
        +List stocks
        +Path output_dir
        +run()
    }
    
    class TradingDirector {
        +Agent director_agent
        +TickrAgent tickr
        +generate_thesis()
    }
    
    class QuantAnalyst {
        +Agent quant_agent
        +analyze()
    }
    
    class RiskManager {
        +Agent risk_agent
        +assess_risk()
    }
    
    class ExecutionAgent {
        +Agent execution_agent
        +generate_order()
    }
    
    AutoHedge --> TradingDirector
    AutoHedge --> QuantAnalyst
    AutoHedge --> RiskManager
    AutoHedge --> ExecutionAgent
```



### API Documentation
To use the API, git clone the repo: 

### 1. Installation
```bash
pip3 install -r requirements.txt
```

### 2. Launch API Server

```bash
python api.py
```

Server will start at `http://localhost:8000`

## API Endpoints

### Authentication
All endpoints except `/users` (POST) require the `X-API-Key` header.

### User Management

#### Create User
```bash
POST /users
Content-Type: application/json

{
    "username": "trader1",
    "email": "trader@example.com",
    "fund_name": "Alpha Fund",
    "fund_description": "AI Trading Strategy"
}
```
Returns API key in response.

#### Get User Profile
```bash
GET /users/me
X-API-Key: your-api-key
```

### Trading Operations

#### Create Trade
```bash
POST /trades
X-API-Key: your-api-key
Content-Type: application/json

{
    "stocks": ["NVDA", "AAPL"],
    "task": "Analyze tech stocks for $1M allocation",
    "allocation": 1000000.0,
    "strategy_type": "momentum",
    "risk_level": 7
}
```

#### List Trades
```bash
GET /trades?limit=10&skip=0&status=completed
X-API-Key: your-api-key
```

#### Get Specific Trade
```bash
GET /trades/{trade_id}
X-API-Key: your-api-key
```

#### Delete Trade
```bash
DELETE /trades/{trade_id}
X-API-Key: your-api-key
```

### Analytics

#### Get Historical Analytics
```bash
GET /analytics/history?days=30
X-API-Key: your-api-key
```

## Quick Test Script

```python
import requests

BASE_URL = "http://localhost:8000"

# Create user and get API key
def get_api_key():
    response = requests.post(
        f"{BASE_URL}/users",
        json={
            "username": "test_trader",
            "email": "test@example.com",
            "fund_name": "Test Fund",
            "fund_description": "Test Strategy"
        }
    )
    return response.json()["api_key"]

# Use the API
api_key = get_api_key()
headers = {"X-API-Key": api_key}

# Create a trade
trade = requests.post(
    f"{BASE_URL}/trades",
    headers=headers,
    json={
        "stocks": ["NVDA"],
        "task": "Test trade",
        "allocation": 1000000.0
    }
)
print(trade.json())
```

## Running in Production
1. Use a production ASGI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

2. Set environment variables:

```bash
export AUTOHEDGE_ENV=production
export AUTOHEDGE_LOG_LEVEL=INFO
```

## Error Codes
- 401: Invalid API key
- 403: Unauthorized access
- 404: Resource not found
- 422: Validation error
- 500: Server error

## Best Practices
1. Store API keys securely
2. Use appropriate error handling
3. Implement rate limiting in production
4. Monitor API usage
5. Regularly backup trade data

## Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`




## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Swarms](https://swarms.ai) for the AI agent framework
- [Tickr Agent](https://github.com/The-Swarm-Corporation/tickr-agent) for market data integration

## 📞 Support

<!-- - Documentation: [https://autohedge.readthedocs.io](https://autohedge.readthedocs.io) -->
- Issue Tracker: [GitHub Issues](https://github.com/The-Swarm-Corporation/AutoHedge/issues)
- Discord: [Join our community](https://swarms.ai)

---
Created with ❤️ by [The Swarm Corporation](https://github.com/The-Swarm-Corporation)
