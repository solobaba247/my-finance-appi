# app.py (V4: High-Performance with Caching)

from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
from cachetools import TTLCache

app = Flask(__name__)

# --- High-Performance Caching ---
# Create a Time-To-Live (TTL) cache.
# maxsize: how many items to store.
# ttl: Time in seconds before an item expires (e.g., 600 seconds = 10 minutes).
# This means data will be fetched from Yahoo Finance at most once every 10 minutes
# for the same request, making subsequent calls instantaneous.
cache = TTLCache(maxsize=1024, ttl=600)

# --- Helper function for fetching and formatting OHLC data ---
# This is now wrapped with our caching logic.
def get_ohlc_data(yfinance_ticker):
    """
    Fetches, validates, and formats OHLC data for a given yfinance ticker.
    This function is now backed by a 10-minute cache to improve performance.
    """
    # Get period and interval from query parameters, with default values
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')

    # Create a unique key for the cache based on the request parameters
    cache_key = f"{yfinance_ticker}-{period}-{interval}"

    # --- Caching Logic ---
    if cache_key in cache:
        print(f"CACHE HIT for {cache_key}")
        return cache[cache_key]

    print(f"CACHE MISS for {cache_key}. Fetching from yfinance...")
    
    # Fetch historical data
    asset = yf.Ticker(yfinance_ticker)
    hist_df = asset.history(period=period, interval=interval, auto_adjust=False)

    # Validate that we received data
    if hist_df.empty:
        error_msg = f"Could not fetch OHLC data for '{yfinance_ticker}'. Check symbol, period ('{period}'), or interval ('{interval}')."
        response = ({"error": error_msg}, 404)
        cache[cache_key] = response # Cache the failure too, to avoid re-requesting bad symbols
        return response
    
    # Format the data for JSON response
    hist_df.reset_index(inplace=True)
    # The date column can be 'Date' or 'Datetime', we handle both
    date_col = 'Date' if 'Date' in hist_df.columns else 'Datetime'
    hist_df.rename(columns={date_col: 'Date'}, inplace=True)
    
    # Make timezone naive before formatting to avoid issues with different timezones from yfinance
    if pd.api.types.is_datetime64_any_dtype(hist_df['Date']) and hist_df['Date'].dt.tz is not None:
         hist_df['Date'] = hist_df['Date'].dt.tz_convert(None)

    hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    data = hist_df.to_dict(orient='records')
    response = (data, 200)

    # Store the successful result in the cache
    cache[cache_key] = response
    return response


@app.route("/")
def hello():
    return "Welcome! Finance API is live. Now with high-performance caching. Try: /api/stock?symbol=AAPL"

# =================================================================
#  INFO ENDPOINTS (No changes needed here, but kept for context)
# =================================================================

# NOTE: For simplicity, I am only showing the OHLC endpoints below as they are the
# ones used by your signal generator's scanner. The "info" endpoints would benefit
# from caching as well, but the OHLC data is the primary performance problem.

# =================================================================
#  OHLC (Historical Data) ENDPOINTS
# =================================================================

@app.route("/api/stock/ohlc")
def get_stock_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/stock/ohlc?symbol=MSFT"}), 400
    
    data, status_code = get_ohlc_data(symbol.upper())
    return jsonify(data), status_code

@app.route("/api/forex/ohlc")
def get_forex_ohlc():
    pair = request.args.get('pair')
    if not pair:
        return jsonify({"error": "The 'pair' query parameter is required. Example: /api/forex/ohlc?pair=EURUSD"}), 400
    
    yfinance_ticker = f"{pair.upper()}=X"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code

@app.route("/api/commodity/ohlc")
def get_commodity_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/commodity/ohlc?symbol=CL"}), 400
        
    yfinance_ticker = f"{symbol.upper()}=F"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code

@app.route("/api/index/ohlc")
def get_index_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/index/ohlc?symbol=DJI"}), 400
    
    yfinance_ticker = f"^{symbol.upper()}"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code
