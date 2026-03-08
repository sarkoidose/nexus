# ⚡ NEXUS — Multi-Agent Financial Intelligence

A sophisticated multi-agent framework for financial market analysis and decision-making. NEXUS orchestrates specialized AI agents that work together to provide comprehensive market insights across multiple asset classes.

```
╔══════════════════════════════════════════════════════════════╗
║         ⚡ NEXUS — Multi-Agent Financial Intelligence ⚡     ║
║      FUNDAMENTUM · MACRO · TECHNICUS · SENTINEL · APEX       ║
╚══════════════════════════════════════════════════════════════╝
```

## 🎯 Overview

NEXUS is a collaborative AI system where multiple specialized agents analyze financial markets from different perspectives:

- **FUNDAMENTUM** — Fundamental analysis and valuation
- **MACRO** — Macroeconomic trends and impact analysis
- **TECHNICUS** — Technical analysis and price patterns
- **SENTINEL** — Risk assessment and market anomalies
- **APEX** — Strategic decisions and portfolio recommendations

## 🚀 Features

- **Multi-Agent Orchestration** — Coordinated analysis from specialized agents
- **Real-time Market Data** — Integration with yfinance for live market data
- **Rich TUI** — Beautiful terminal interface with Rich library
- **Comprehensive Analysis** — Fundamental, technical, macro, and risk perspectives
- **Decision Framework** — Unified consensus-based decision making
- **Analysis History** — Track and save historical analyses

## 📋 Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`:
  - `rich` — Beautiful terminal output
  - `httpx` — Async HTTP client
  - `yfinance` — Yahoo Finance data
  - `numpy` — Numerical computing

## 💾 Installation

```bash
# Clone the repository
git clone https://github.com/sarkoidose/nexus.git
cd nexus

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🎮 Usage

```bash
python3 nexus.py
```

The interactive interface will guide you through:

1. **Market Selection** — Choose asset classes to analyze
2. **Agent Analysis** — Wait for all agents to complete their analysis
3. **Decision** — View consensus recommendation and individual perspectives
4. **History** — Review previous analyses

### Example Workflow

```bash
$ python3 nexus.py

# Select assets (e.g., AAPL, BTC-USD, SPY)
# Agents analyze simultaneously
# Review consolidated decision
# Save analysis to file
```

## 📁 Project Structure

```
nexus/
├── nexus.py              # Main entry point
├── requirements.txt      # Python dependencies
├── config/
│   └── settings.py       # Configuration and constants
├── core/
│   ├── base_agent.py     # Base agent class
│   └── orchestrator.py   # Multi-agent orchestration
├── agents/
│   ├── apex.py           # Apex agent (strategy)
│   └── specialists.py    # Specialist agents (FUNDAMENTUM, MACRO, etc.)
└── tui/
    └── display.py        # Terminal UI and rendering
```

## 🔧 Configuration

Edit `config/settings.py` to customize:

- **ASSET_CLASSES** — Available financial instruments
- **Agent parameters** — Thresholds and settings
- **Output paths** — Where analyses are saved

## 📊 Analysis Output

Each analysis generates:

- Individual agent reports (scores, recommendations)
- Consensus decision (BUY/HOLD/SELL)
- Risk assessment
- Supporting rationale
- JSON export for programmatic use

## 🛠 Development

### Run Tests

```bash
# Syntax check
bash -n nexus.py
```

### Debug Mode

```bash
# Run with debug output
bash -x nexus.py
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional specialized agents
- More data sources integration
- Enhanced consensus algorithms
- Performance optimizations

## 📄 License

MIT

## 🎨 Author

Created for advanced financial analysis and multi-agent AI research.

---

**Made with ⚡ and 🤖**
