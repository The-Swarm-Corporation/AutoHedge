# 🚀 AutoHedge - 5 Minute Quickstart

Get AutoHedge running locally with a user-friendly web interface in just a few steps!

## What You'll Get

- ✅ A beautiful web interface to analyze stocks
- ✅ AI-powered trading analysis with multiple specialized agents
- ✅ Real-time market data integration
- ✅ Risk assessment and trade recommendations

## Prerequisites

- Python 3.8+ installed
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys) - Free tier available)

## Setup in 3 Steps

### Step 1: Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Configure AutoHedge

Create a file named `.env` in the AutoHedge directory with:

```bash
OPENAI_API_KEY=your_api_key_here
WORKSPACE_DIR=agent_workspace
OUTPUT_DIR=outputs
```

Replace `your_api_key_here` with your actual API key.

### Step 3: Run AutoHedge

**Option A: Automated (Easiest)**
```bash
./start_autohedge.sh
```

**Option B: Manual**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Start the API server
python3 api/api.py
```

Then open `web_ui.html` in your browser!

## 🎯 Try Your First Analysis

1. **Open the Web Interface**: `web_ui.html` in your browser
2. **Enter a stock**: For example, `NVDA`
3. **Describe your goal**: "Analyze NVDA for a $50k investment with moderate risk"
4. **Set allocation**: `50000`
5. **Click "Analyze Stocks"**

Wait about 30-60 seconds while the AI agents:
- Fetch real-time market data
- Generate trading thesis
- Perform quantitative analysis
- Assess risks
- Generate recommendations

## 📊 Example Analyses You Can Run

### Tech Stock Analysis
```
Stocks: NVDA, AAPL, MSFT
Task: Analyze these tech giants for a $100k portfolio focused on growth
Allocation: 100000
```

### Conservative Portfolio
```
Stocks: JNJ, PG, KO
Task: Evaluate defensive stocks for a conservative $200k retirement portfolio
Allocation: 200000
```

### Growth Opportunity
```
Stocks: TSLA, AMD, PLTR
Task: Identify high-growth opportunities for aggressive $50k allocation
Allocation: 50000
```

## 🎓 Understanding Your Results

The analysis shows outputs from 4 specialized AI agents:

1. **📈 Trading Director**: Market analysis and overall strategy
2. **🔢 Quant Agent**: Technical indicators and probability scores
3. **⚠️ Risk Manager**: Risk assessment and position sizing
4. **💼 Execution Agent**: Specific trade recommendations

Each provides their expert perspective on your investment!

## ⚡ Quick Tips

- ✅ Be specific in your task description
- ✅ Include your risk tolerance (conservative/moderate/aggressive)
- ✅ Start with 1-3 stocks for faster results
- ✅ First run may take longer as agents initialize

## 🆘 Troubleshooting

**"API Disconnected" in web UI?**
- Make sure `python3 api/api.py` is running
- Check http://localhost:8000/docs loads

**"Invalid API Key" error?**
- Verify your OpenAI API key in `.env`
- Check for extra spaces
- Ensure you have credits in your OpenAI account

**Dependencies won't install?**
- Update pip: `pip3 install --upgrade pip`
- Try: `pip3 install -r requirements.txt --no-cache-dir`

## 🎉 You're Ready!

For detailed documentation, see [SETUP_LOCAL.md](SETUP_LOCAL.md)

For API details, visit http://localhost:8000/docs after starting the server

---

**Pro Tip**: The web interface automatically creates an API session for you - no manual API key management needed!
