# app.py (V6: Added Health Check)

from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
from cachetools import TTLCache
import re

app = Flask(__name__)

# --- High-Performance Caching ---
cache = TTLCache(maxsize=1024, ttl=600)

# --- Helper function for fetching and formatting OHLC data ---
def get_ohlc_data(yfinance_ticker):
    """
    Fetches, validates, and formats OHLC data for a given yfinance ticker.
    This function is now backed by a 10-minute cache to improve performance.
    """
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')

    # --- FIX: Added validation for intraday data requests ---
    # yfinance intraday data is limited to a 60-day lookback period.
    if interval.endswith('m') or interval.endswith('h'): # e.g., '1m', '5m', '1h'
        # Extract the number from the period string (e.g., '60d' -> 60)
        period_value = int(re.findall(r'(\d+)', period)[0]) if re.findall(r'(\d+)', period) else 0
        period_unit = period[-1]

        # Convert period to an approximate number of days
        days_requested = 0
        if period_unit == 'd':
            days_requested = period_value
        elif period_unit == 'o': # 'mo'
            days_requested = period_value * 30
        
        # Yahoo Finance limit is 60 days for intraday
        if days_requested > 60:
            error_msg = f"Invalid request. Intraday data (interval '{interval}') is only available for periods up to 60 days. Please use a shorter period like '60d' or '1mo'."
            # Do NOT cache this user error, as they might want to correct it
            return ({"error": error_msg}, 400) # 400 for Bad Request

    cache_key = f"{yfinance_ticker}-{period}-{interval}"

    # --- Caching Logic ---
    if cache_key in cache:
        print(f"CACHE HIT for {cache_key}")
        return cache[cache_key]

    print(f"CACHE MISS for {cache_key}. Fetching from yfinance...")
    
    asset = yf.Ticker(yfinance_ticker)
    hist_df = asset.history(period=period, interval=interval, auto_adjust=False)

    if hist_df.empty:
        error_msg = f"Could not fetch OHLC data for '{yfinance_ticker}'. Check symbol, period ('{period}'), or interval ('{interval}')."
        response = ({"error": error_msg}, 404)
        cache[cache_key] = response # Cache the failure
        return response
    
    hist_df.reset_index(inplace=True)
    date_col = 'Date' if 'Date' in hist_df.columns else 'Datetime'
    hist_df.rename(columns={date_col: 'Date'}, inplace=True)
    
    if pd.api.types.is_datetime64_any_dtype(hist_df['Date']) and hist_df['Date'].dt.tz is not None:
         hist_df['Date'] = hist_df['Date'].dt.tz_convert(None)

    # --- FIX: Changed date format to standard ISO 8601 ---
    hist_df['Date'] = pd.to_datetime(hist_df['Date']).dt.isoformat()
    
    data = hist_df.to_dict(orient='records')
    response = (data, 200)
    cache[cache_key] = response
    return response


@app.route("/")
def hello():
    return "Welcome! Finance API is live. Now with high-performance caching. Try: /api/stock/ohlc?symbol=AAPL"

@app.route("/health")
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy"}), 200

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
