# Binance Futures Trading Bot 🤖

A Python trading bot for Binance Futures Testnet with advanced order execution capabilities.

## Features ✨

- **Order Types Supported**:
  - Market Orders
  - Limit Orders
  - Stop Orders
  - Stop-Limit Orders
  - Trailing Stop Orders (Bonus)

- **Key Functionality**:
  - Real-time balance checking
  - Comprehensive error handling
  - Detailed logging
  - CLI interface

## Prerequisites 📋

- Python 3.8+
- Binance Testnet Account ([Register Here](https://testnet.binancefuture.com))
- API Keys with Futures Trading permissions

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/ManyaShah1/BinanceTradingBOT.git
cd BinanceTradingBOT


 ## BASIC COMMANDS 

 
# Market order
python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Limit order
python main.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 2500

# Stop-Limit order
python main.py --symbol SOLUSDT --side SELL --type STOP_LIMIT --quantity 5 --price 90 --stop_price 89


