# update_data.py
import yfinance as yf
import json
from datetime import datetime

# List of tickers we want to track
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"]

def fetch_stock_data():
    """Fetches the latest price for a list of tickers."""
    print("Fetching latest stock data...")
    data = {}
    
    for ticker_symbol in TICKERS:
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # Check if we got valid data
            if 'currentPrice' in info and info['currentPrice'] is not None:
                data[ticker_symbol] = {
                    "price": info['currentPrice'],
                    "companyName": info.get('longName', 'N/A')
                }
                print(f"Successfully fetched {ticker_symbol}: {info['currentPrice']}")
            else:
                # Use 'fast_info' as a fallback for some symbols
                price = stock.fast_info.get('last_price')
                if price:
                    data[ticker_symbol] = {
                        "price": price,
                        "companyName": stock.fast_info.get('long_name', 'N/A')
                    }
                    print(f"Successfully fetched {ticker_symbol} (using fast_info): {price}")
                else:
                    print(f"Could not fetch data for {ticker_symbol}")

        except Exception as e:
            print(f"An error occurred while fetching {ticker_symbol}: {e}")

    return data

def main():
    stock_data = fetch_stock_data()
    
    if not stock_data:
        print("No data fetched. Exiting without writing file.")
        return

    # Create a structured dictionary with a timestamp
    output_data = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "stocks": stock_data
    }

    # Write the data to a file named 'live_data.json'
    with open("live_data.json", "w") as f:
        json.dump(output_data, f, indent=4)
        
    print("Data successfully written to live_data.json")

if __name__ == "__main__":
    main()
