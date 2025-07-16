import yfinance as yf
import json
from datetime import datetime, timezone
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]

def fetch_stock_data():
    """Fetches the latest price with improved error handling."""
    logger.info("Starting stock data fetch...")
    data = {}
    
    for ticker_symbol in TICKERS:
        try:
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(0.2, 0.5))
            
            stock = yf.Ticker(ticker_symbol)
            
            # Try multiple data sources
            price = None
            company_name = "N/A"
            
            # Try info first
            try:
                info = stock.info
                if info and 'currentPrice' in info and info['currentPrice']:
                    price = info['currentPrice']
                    company_name = info.get('longName', 'N/A')
            except:
                pass
            
            # Try fast_info as fallback
            if price is None:
                try:
                    fast_info = stock.fast_info
                    price = fast_info.get('last_price')
                    company_name = fast_info.get('long_name', 'N/A')
                except:
                    pass
            
            # Try history as last resort
            if price is None:
                try:
                    hist = stock.history(period='1d', interval='1d')
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                except:
                    pass
            
            if price is not None:
                data[ticker_symbol] = {
                    "price": float(price),
                    "companyName": company_name,
                    "fetchTime": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"✓ {ticker_symbol}: ${price:.2f}")
            else:
                logger.warning(f"✗ Could not fetch data for {ticker_symbol}")
                
        except Exception as e:
            logger.error(f"✗ Error fetching {ticker_symbol}: {str(e)}")
    
    return data

def main():
    stock_data = fetch_stock_data()
    
    if not stock_data:
        logger.error("No data fetched. Exiting.")
        return
    
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "data_count": len(stock_data),
        "stocks": stock_data
    }
    
    try:
        with open("live_data.json", "w") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"✓ Data written to live_data.json ({len(stock_data)} stocks)")
    except Exception as e:
        logger.error(f"✗ Error writing file: {str(e)}")

if __name__ == "__main__":
    main()
