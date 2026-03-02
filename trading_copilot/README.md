# Trading Copilot

An intelligent research assistant for stock sentiment analysis.

## Overview

Trading Copilot takes a stock ticker as input and uses multiple specialized agents to research:
- Market news
- Company earnings calls
- Macro-economic trends (geo-political tensions, interest rates, etc.)

It then aggregates all research, analyzes the data, and provides a high-level sentiment (bullish or bearish) for the upcoming 1-2 weeks.

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Usage

```python
from trading_copilot.validator import TickerValidator

validator = TickerValidator()
result = validator.validate("AAPL")
print(result)
```

## Configuration

Data sources are configured in `config/sources.yaml`. Each agent type supports multiple data sources for redundancy.

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=trading_copilot
```

## Disclaimer

This tool is for informational purposes only and does not constitute financial advice.
