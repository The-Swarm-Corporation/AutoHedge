# AutoHedge Local Setup Guide

This guide will help you run AutoHedge locally on your computer with an easy-to-use web interface.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

## 🚀 Quick Start (Automated)

### Option 1: Using the Startup Script (Recommended)

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/The-Swarm-Corporation/AutoHedge.git
   cd AutoHedge
   ```

2. **Run the startup script**:
   ```bash
   chmod +x start_autohedge.sh
   ./start_autohedge.sh
   ```

3. **Follow the prompts** to set up your OpenAI API key

4. **Access the Web UI** - it will open automatically, or go to:
   - Open `web_ui.html` in your browser

That's it! The script handles everything else.

## 🔧 Manual Setup

If you prefer to set things up manually:

### Step 1: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 2: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   WORKSPACE_DIR=agent_workspace
   OUTPUT_DIR=outputs
   ```

### Step 3: Create Required Directories

```bash
mkdir -p outputs logs agent_workspace
```

### Step 4: Start the API Server

```bash
python3 api/api.py
```

The API server will start on `http://localhost:8000`

### Step 5: Open the Web Interface

Open `web_ui.html` in your web browser. You can:
- Double-click the file
- Or use: `open web_ui.html` (Mac) or `xdg-open web_ui.html` (Linux)

## 🎯 Using AutoHedge

### Web Interface

1. **Enter Stock Symbols**: Type one or more stock symbols (e.g., NVDA, AAPL, TSLA)
2. **Describe Your Task**: Enter what you want to analyze (e.g., "Analyze for a $100k portfolio")
3. **Set Allocation**: Enter your investment amount
4. **Click "Analyze Stocks"**: Wait for the AI agents to analyze

The system will:
- Fetch real-time market data
- Generate trading theses
- Perform quantitative analysis
- Assess risks
- Provide recommendations

### Example Task

```
Stocks: NVDA, AAPL
Task: Analyze these stocks for a $50,000 balanced portfolio with moderate risk tolerance
Allocation: 50000
```

## 📊 Understanding the Results

The analysis includes outputs from multiple specialized AI agents:

1. **Trading Director**: Overall strategy and market thesis
2. **Quant Agent**: Technical analysis and probability scores
3. **Risk Manager**: Risk assessment and position sizing
4. **Execution Agent**: Trade order recommendations

## 🛠️ Troubleshooting

### API Won't Start

**Problem**: API server fails to start

**Solutions**:
- Check if port 8000 is already in use: `lsof -i :8000`
- Kill any existing process: `kill $(lsof -t -i:8000)`
- Try a different port in `api/api.py`

### Missing Dependencies

**Problem**: Import errors when starting

**Solution**:
```bash
pip3 install --upgrade -r requirements.txt
```

### API Key Issues

**Problem**: "Invalid API key" or authentication errors

**Solutions**:
- Verify your OpenAI API key is correct
- Check `.env` file exists and is properly formatted
- Ensure no extra spaces in the API key
- Make sure you have credits in your OpenAI account

### Connection Issues in Web UI

**Problem**: "API Disconnected" message

**Solutions**:
- Ensure API server is running (`python3 api/api.py`)
- Check if you can access http://localhost:8000/docs
- Clear browser cache and reload
- Check firewall settings

## 🔐 Security Notes

- **Never commit your `.env` file** to version control
- Keep your API keys private
- The `.env` file is already in `.gitignore`
- API keys are generated per-session in the web UI

## 📁 Directory Structure

```
AutoHedge/
├── api/
│   └── api.py              # FastAPI server
├── autohedge/
│   └── main.py             # Core trading logic
├── outputs/                # Analysis results
├── logs/                   # System logs
├── web_ui.html            # Web interface
├── start_autohedge.sh     # Startup script
├── .env                   # Your configuration (create from .env.example)
└── requirements.txt       # Python dependencies
```

## 🎓 Advanced Usage

### Using the Python API Directly

```python
from autohedge.main import AutoHedge

# Initialize
trading_system = AutoHedge(
    stocks=["NVDA", "AAPL"],
    name="my-fund",
    description="My trading strategy"
)

# Run analysis
result = trading_system.run(
    task="Analyze for $100k allocation with moderate risk"
)

print(result)
```

### API Endpoints

The FastAPI server provides REST endpoints:

- `POST /users` - Create user and get API key
- `POST /trades` - Submit trading analysis request
- `GET /trades` - List your trades
- `GET /trades/{id}` - Get specific trade
- `GET /analytics/history` - Get historical analytics

Full API documentation: http://localhost:8000/docs

## 🆘 Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Review [API documentation](http://localhost:8000/docs)
- Open an issue on [GitHub](https://github.com/The-Swarm-Corporation/AutoHedge/issues)
- Join the [Discord community](https://discord.gg/agora-999382051935506503)

## 📝 Notes

- First analysis may take 1-2 minutes as agents initialize
- Market data is fetched in real-time
- Analysis quality depends on market conditions and data availability
- This is for educational and analysis purposes - always do your own research before trading

## ⚡ Performance Tips

- Use specific, clear task descriptions
- Limit to 3-5 stocks per analysis for faster results
- Close other applications to free up memory
- Ensure stable internet connection for API calls

---

**Happy Trading! 🚀**
