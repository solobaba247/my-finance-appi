# Add proper error handling and logging
import logging
from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
from cachetools import TTLCache
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Improved error handling in get_ohlc_data
def get_ohlc_data(yfinance_ticker):
    try:
        # ... existing code ...
        
        asset = yf.Ticker(yfinance_ticker)
        hist_df = asset.history(period=period, interval=interval, auto_adjust=False)
        
        if hist_df.empty:
            logger.warning(f"No data returned for {yfinance_ticker}")
            error_msg = f"No data available for '{yfinance_ticker}'"
            response = ({"error": error_msg}, 404)
            return response
            
        # ... rest of processing ...
        
    except Exception as e:
        logger.error(f"Error fetching data for {yfinance_ticker}: {str(e)}")
        error_msg = f"Server error while fetching data for '{yfinance_ticker}'"
        return ({"error": error_msg}, 500)

# Add health check endpoint
@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
