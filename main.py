import logging
from binance import Client
from binance.exceptions import BinanceAPIException
import argparse
import time
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Union

# Load environment variables
load_dotenv()

class BinanceFuturesBot:
    """A trading bot for Binance Futures with enhanced features."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the trading bot with API credentials.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: True)
        """
        self.session = None
        self._setup_logging()
        self.client = self._initialize_client(api_key, api_secret, testnet)
        self.logger.info(f"Bot initialized in {'TESTNET' if testnet else 'LIVE'} mode")

    def _setup_logging(self) -> None:
        """Configure logging for the bot."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BinanceFuturesBot')

    def _initialize_client(self, api_key: str, api_secret: str, testnet: bool) -> Client:
        """Initialize and verify Binance client connection."""
        try:
            client = Client(
                api_key,
                api_secret,
                testnet=testnet,
                requests_params={'timeout': 30},
                tld='com',
            )
            
            # Test connection
            client.futures_account()
            self.logger.info("✅ Successfully connected to Binance Futures API")
            return client
            
        except BinanceAPIException as e:
            self.logger.error(f" API Connection Failed: {e.status_code} - {e.message}")
            raise
        except Exception as e:
            self.logger.error(f" Unexpected connection error: {str(e)}")
            raise

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trailing_delta: Optional[int] = None
    ) -> Dict:
        """Place an order on Binance Futures."""
        try:
            # Correct order type mapping
            type_map = {
                'MARKET': 'MARKET',
                'LIMIT': 'LIMIT',
                'STOP': 'STOP_MARKET',
                'TRAILING_STOP': 'TRAILING_STOP_MARKET'
            }
            
            params = {
                'symbol': symbol.upper(),
                'side': side,
                'type': type_map.get(order_type, order_type),
                'quantity': quantity,
                'timestamp': int(time.time() * 1000)
            }
            
            # Add conditional parameters
            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
                
            if stop_price:
                params['stopPrice'] = stop_price
                
            if trailing_delta:
                params['activationPrice'] = stop_price
                params['callbackRate'] = trailing_delta
                params['workingType'] = 'MARK_PRICE'
                
            self.logger.info(f"Placing order with params: {params}")
            
            # Special handling for trailing stop
            response = self.client.futures_create_order(**params)
            
            self.logger.info(f"Order placed successfully: {response}")
            return response
            
        except BinanceAPIException as e:
            self.logger.error(f"API Error {e.status_code}: {e.message}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def _validate_quantity(self, symbol: str, quantity: float) -> float:
        """Validate quantity against Binance's LOT_SIZE rules."""
        info = self.client.futures_exchange_info()
        for symbol_info in info['symbols']:
            if symbol_info['symbol'] == symbol:
                for filter in symbol_info['filters']:
                    if filter['filterType'] == 'LOT_SIZE':
                        min_qty = float(filter['minQty'])
                        max_qty = float(filter['maxQty'])
                        step_size = float(filter['stepSize'])
                        
                        if quantity < min_qty or quantity > max_qty:
                            raise ValueError(
                                f"Quantity must be between {min_qty} and {max_qty}"
                            )
                            
                        # Round to step size
                        return round(quantity / step_size) * step_size
        return quantity

    def get_balance(self, asset: str = 'USDT') -> float:
        """Get available futures balance for an asset."""
        try:
            balance = next(
                (item for item in self.client.futures_account_balance() 
                 if item['asset'] == asset),
                None
            )
            return float(balance['availableBalance']) if balance else 0.0
        except Exception as e:
            self.logger.error(f" Failed to get balance: {str(e)}")
            raise

def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not args.symbol.isupper():
        raise ValueError("Symbol must be uppercase (e.g., BTCUSDT)")
        
    if args.type == 'LIMIT' and not args.price:
        raise ValueError("Limit orders require --price")
        
    if args.type == 'STOP' and not args.stop_price:
        raise ValueError("Stop orders require --stop_price")
        
    if args.type == 'TRAILING_STOP' and not args.trailing_delta:
        raise ValueError("Trailing stop orders require --trailing_delta")
        
    if args.quantity <= 0:
        raise ValueError("Quantity must be positive")

def main():
    """Main entry point for the trading bot."""
    parser = argparse.ArgumentParser(
        description='Binance Futures Trading Bot',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--symbol', required=True, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('--side', required=True, choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('--type', required=True, 
                       choices=['MARKET', 'LIMIT', 'STOP', 'TRAILING_STOP'], 
                       help='Order type')
    parser.add_argument('--quantity', type=float, required=True, help='Order quantity')
    
    # Conditional arguments
    parser.add_argument('--price', type=float, help='Price for LIMIT orders')
    parser.add_argument('--stop_price', type=float, help='Stop price for STOP orders')
    parser.add_argument('--trailing_delta', type=int, 
                       help='Callback rate (1-100) for TRAILING_STOP orders')
    
    # API configuration
    parser.add_argument('--api_key', help='Binance API key (optional if in .env)')
    parser.add_argument('--api_secret', help='Binance API secret (optional if in .env)')
    parser.add_argument('--testnet', action='store_true', default=True,
                       help='Use testnet (default)')
    parser.add_argument('--live', action='store_false', dest='testnet',
                       help='Use live exchange')
    
    args = parser.parse_args()
    
    try:
        validate_args(args)
        
        # Load configuration
        api_key = args.api_key or os.getenv("BINANCE_API_KEY")
        api_secret = args.api_secret or os.getenv("BINANCE_API_SECRET")
        
        if not api_key or not api_secret:
            raise ValueError("API keys must be provided via CLI or .env file")
        
        # Initialize bot
        bot = BinanceFuturesBot(api_key, api_secret, args.testnet)
        
        # Display balance before trading
        balance = bot.get_balance()
        print(f"\n💰 Available USDT balance: {balance:.2f}")
        
        # Place order
        response = bot.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            trailing_delta=args.trailing_delta
        )
        
        # Display order results
        print("\n🎯 Order Result:")
        print(f"Order ID: {response['orderId']}")
        print(f"Symbol: {response['symbol']}")
        print(f"Type: {response['type']}")
        print(f"Side: {response['side']}")
        print(f"Quantity: {response['origQty']}")
        print(f"Status: {response['status']}")
        if 'price' in response:
            print(f"Price: {response['price']}")
        if 'stopPrice' in response:
            print(f"Stop Price: {response['stopPrice']}")
        
    except Exception as e:
        print(f"\n Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()