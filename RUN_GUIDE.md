# 🎯 Complete Guide to Running AutoHedge Locally

This guide will walk you through everything step-by-step to get AutoHedge running on your computer.

## 📋 What You Need

- A computer with Python 3.8 or newer
- Internet connection
- An OpenAI API key (I'll show you how to get one)
- 5-10 minutes

---

## Step 1: Get Your OpenAI API Key (2 minutes)

### If You Already Have an OpenAI Account:

1. Go to: https://platform.openai.com/api-keys
2. Log in with your OpenAI account
3. Click the **"+ Create new secret key"** button
4. Give it a name like "AutoHedge"
5. Click **"Create secret key"**
6. **IMPORTANT**: Copy the key immediately (starts with `sk-...`)
   - You can only see it once!
   - Save it somewhere safe temporarily

### If You Don't Have an OpenAI Account:

1. Go to: https://platform.openai.com/signup
2. Sign up with your email or Google account
3. Verify your email
4. Add a payment method (required, but charges are minimal)
   - You get free credits to start
   - Analysis costs are typically $0.10-$0.50 per run
5. Then follow the steps above to create an API key

**💡 Tip**: OpenAI usually gives you $5-$10 in free credits to start!

---

## Step 2: Download/Clone AutoHedge (1 minute)

If you don't have the repository yet:

```bash
git clone https://github.com/The-Swarm-Corporation/AutoHedge.git
cd AutoHedge
```

If you already have it, make sure you're in the AutoHedge directory:

```bash
cd AutoHedge
```

---

## Step 3: Set Up Your Environment (2 minutes)

### Create Your .env File

**Option A: Copy the template**
```bash
cp .env.example .env
```

**Option B: Create it manually**
```bash
nano .env
```
Or use any text editor you prefer.

### Add Your API Key

Open the `.env` file and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
WORKSPACE_DIR=agent_workspace
OUTPUT_DIR=outputs
```

**Replace `sk-your-actual-key-here` with the actual key you copied in Step 1.**

Save the file:
- In nano: Press `Ctrl+X`, then `Y`, then `Enter`
- In other editors: Just save normally

### 🔒 Security Check

Make sure your `.env` file won't be committed to git:

```bash
git status
```

You should **NOT** see `.env` in the list. If you do, something is wrong.
Only `.env.example` should appear in git.

---

## Step 4: Install Dependencies (2-3 minutes)

Install the required Python packages:

```bash
pip3 install -r requirements.txt
```

**If you get permission errors**, try:
```bash
pip3 install --user -r requirements.txt
```

**If pip3 is not found**, you might need to install pip:
```bash
# On Ubuntu/Debian
sudo apt-get install python3-pip

# On Mac
python3 -m ensurepip --upgrade
```

This will install:
- swarms (AI agent framework)
- tickr-agent (stock market data)
- fastapi & uvicorn (web server)
- And other dependencies

---

## Step 5: Start AutoHedge (1 minute)

### Automated Method (Recommended)

Run the startup script:

```bash
chmod +x start_autohedge.sh
./start_autohedge.sh
```

This script will:
- ✅ Check your setup
- ✅ Create necessary directories
- ✅ Start the API server
- ✅ Try to open the web interface automatically

### Manual Method

If the script doesn't work for you:

```bash
# Create necessary directories
mkdir -p outputs logs agent_workspace

# Start the API server
python3 api/api.py
```

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Leave this terminal window open!** The server needs to keep running.

---

## Step 6: Open the Web Interface (30 seconds)

### Method 1: Direct File Open
1. Navigate to the AutoHedge folder in your file browser
2. Find `web_ui.html`
3. Double-click it to open in your browser

### Method 2: From Terminal

**On Mac:**
```bash
open web_ui.html
```

**On Linux:**
```bash
xdg-open web_ui.html
```

**On Windows:**
```bash
start web_ui.html
```

### Method 3: Manual Browser Open
1. Open your web browser (Chrome, Firefox, Safari, etc.)
2. Press `Ctrl+O` (or `Cmd+O` on Mac)
3. Navigate to the AutoHedge folder
4. Select `web_ui.html`

---

## Step 7: Run Your First Analysis (2 minutes)

You should now see the AutoHedge web interface!

### Check Connection

At the top of the page, you should see:
- ✅ Green badge: "API Connected" - Great! You're ready!
- ❌ Red badge: "API Disconnected" - The server isn't running. Go back to Step 5.

### Try an Example Analysis

The form is pre-filled with example values. Let's try it:

1. **Stock Symbols**: `NVDA` (or change to any stock you want)
2. **Analysis Task**: `Analyze NVDA for a balanced portfolio with moderate risk tolerance`
3. **Allocation Amount**: `50000` (that's $50,000)
4. Click **"Analyze Stocks"**

### What Happens Next

You'll see a loading spinner that says "Analyzing stocks with AI agents..."

This typically takes **30-90 seconds** because:
- 🔍 Fetches real-time market data for the stock
- 🤖 4 AI agents analyze the data
- 📊 Generates comprehensive recommendations

### Understanding Your Results

When complete, you'll see results from 4 AI agents:

1. **Trading Director** - Overall market analysis and strategy
2. **Quant Agent** - Technical analysis and probability scores
3. **Risk Manager** - Risk assessment and position sizing
4. **Execution Agent** - Specific trade recommendations

Each agent provides their expert analysis!

---

## 📊 More Example Analyses to Try

### Conservative Portfolio
```
Stocks: JNJ, PG, KO
Task: Evaluate these defensive stocks for a conservative $200k retirement portfolio
Allocation: 200000
```

### Tech Growth
```
Stocks: NVDA, AAPL, MSFT, GOOGL
Task: Analyze tech giants for a $100k growth-focused portfolio
Allocation: 100000
```

### High Risk/High Reward
```
Stocks: TSLA, AMD, PLTR
Task: Identify aggressive growth opportunities for a $30k speculative investment
Allocation: 30000
```

### Single Stock Deep Dive
```
Stocks: AAPL
Task: Should I buy Apple stock now? I have $25k to invest and moderate risk tolerance
Allocation: 25000
```

---

## 🛠️ Troubleshooting

### "API Disconnected" Error

**Problem**: Web UI shows "API Disconnected"

**Solutions**:
1. Make sure the API server is running (Step 5)
2. Check if you can access http://localhost:8000/docs in your browser
3. Try restarting the server:
   ```bash
   # Stop the server (Ctrl+C in the terminal)
   # Start it again
   python3 api/api.py
   ```

### Port 8000 Already in Use

**Problem**: Error says port 8000 is already in use

**Solution**: Kill the existing process:
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (replace PID with the actual process ID)
kill -9 PID

# Or kill all Python processes (careful!)
pkill -f "python3 api/api.py"
```

### "Invalid API Key" or OpenAI Errors

**Problem**: Analysis fails with API key errors

**Solutions**:
1. Check your `.env` file has the correct API key
2. Make sure there are no extra spaces before/after the key
3. Verify the key is active at https://platform.openai.com/api-keys
4. Check you have credits in your OpenAI account
5. Restart the API server after changing `.env`:
   ```bash
   # Stop with Ctrl+C, then start again
   python3 api/api.py
   ```

### Dependencies Won't Install

**Problem**: `pip3 install` fails

**Solutions**:
```bash
# Update pip first
pip3 install --upgrade pip

# Try installing again
pip3 install -r requirements.txt

# If still failing, try without cache
pip3 install -r requirements.txt --no-cache-dir

# Or install as user
pip3 install --user -r requirements.txt
```

### Python Version Too Old

**Problem**: Error about Python version

**Check your version**:
```bash
python3 --version
```

You need Python 3.8 or newer.

**Update Python**:
- **Mac**: `brew install python3`
- **Ubuntu**: `sudo apt-get install python3.10`
- **Windows**: Download from python.org

### Browser Won't Open web_ui.html

**Problem**: File opens as text instead of webpage

**Solution**:
1. Right-click `web_ui.html`
2. Select "Open with..."
3. Choose your web browser (Chrome, Firefox, etc.)

### Analysis Takes Too Long

**Problem**: Stuck on "Analyzing..."

**Normal**: First analysis can take 1-2 minutes
**If stuck 5+ minutes**:
1. Check the API server terminal for errors
2. Check your internet connection
3. Restart the server and try again
4. Try with just one stock instead of multiple

### Results Look Weird or Empty

**Problem**: Results don't display properly

**Solutions**:
1. Try a different web browser
2. Clear your browser cache (Ctrl+Shift+Delete)
3. Check the browser console (F12) for JavaScript errors
4. Make sure JavaScript is enabled in your browser

---

## 🔄 How to Stop and Restart

### Stopping AutoHedge

**In the terminal where API is running**:
- Press `Ctrl+C`

**Or kill from another terminal**:
```bash
pkill -f "python3 api/api.py"
```

### Restarting AutoHedge

Simply run the start command again:
```bash
./start_autohedge.sh
```

Or manually:
```bash
python3 api/api.py
```

Then refresh `web_ui.html` in your browser.

---

## 📁 Where Are My Results?

Analysis results are stored in:
- **outputs/** - JSON files with full analysis
- **logs/** - System logs and debugging info
- **agent_workspace/** - Temporary agent data

You can view these files to see detailed analysis history.

---

## 💡 Pro Tips

1. **Be Specific**: The more detailed your task description, the better the analysis
   - ✅ Good: "Analyze NVDA for a $50k tech-focused portfolio with 5-year horizon and moderate risk"
   - ❌ Vague: "Should I buy NVDA?"

2. **Start Small**: Try 1-2 stocks first to get faster results

3. **Include Context**: Mention your risk tolerance, investment horizon, and goals

4. **Save Good Queries**: Keep a note of task descriptions that work well

5. **Check Logs**: If something goes wrong, check `logs/` directory for details

---

## 🔒 Security Best Practices

1. ✅ **Never commit your .env file** - it's already in .gitignore
2. ✅ **Don't share your API key** - treat it like a password
3. ✅ **Rotate your key periodically** - create new keys at OpenAI
4. ✅ **Monitor your usage** - check OpenAI dashboard for costs
5. ✅ **Use environment variables** - never hardcode API keys in code

---

## 💰 Cost Information

### Typical Costs Per Analysis:

- **Single stock**: $0.10 - $0.30
- **Multiple stocks**: $0.30 - $0.80
- **Complex analysis**: $0.50 - $1.50

### To Monitor Costs:

1. Go to https://platform.openai.com/usage
2. View your API usage
3. Set up spending limits if desired

**💡 Tip**: Start with the free credits OpenAI provides!

---

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **Explore the API**: Visit http://localhost:8000/docs for API documentation
2. **Read the Code**: Check `autohedge/main.py` to understand the agents
3. **Customize**: Modify prompts or add new agents
4. **Use Programmatically**: Import AutoHedge in your Python scripts

---

## 📞 Getting Help

If you're still stuck:

1. **Check Documentation**:
   - [README.md](README.md) - Project overview
   - [SETUP_LOCAL.md](SETUP_LOCAL.md) - Detailed setup
   - [QUICKSTART.md](QUICKSTART.md) - Quick reference

2. **Check the Logs**:
   ```bash
   tail -f logs/autohedge_*.log
   ```

3. **Community Support**:
   - GitHub Issues: https://github.com/The-Swarm-Corporation/AutoHedge/issues
   - Discord: https://discord.gg/agora-999382051935506503

4. **Check API Status**: http://localhost:8000/docs

---

## ✅ Quick Reference Commands

```bash
# Start AutoHedge (automated)
./start_autohedge.sh

# Start AutoHedge (manual)
python3 api/api.py

# Stop AutoHedge
# Press Ctrl+C in the terminal, or:
pkill -f "python3 api/api.py"

# View logs
tail -f logs/autohedge_*.log

# Install/Update dependencies
pip3 install -r requirements.txt

# Check if server is running
curl http://localhost:8000/docs

# Open web interface
open web_ui.html  # Mac
xdg-open web_ui.html  # Linux
start web_ui.html  # Windows
```

---

## 🎉 You're All Set!

You now have everything you need to run AutoHedge locally and analyze stocks with AI!

**Happy trading! 📈🚀**

---

*Remember: AutoHedge provides analysis and recommendations, but you should always do your own research and consider consulting with a financial advisor before making investment decisions.*
