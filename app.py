# app.py (V10: Added dedicated endpoint for the market scanner)

from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd
from cachetools import TTLCache
import re
import json

app = Flask(__name__)

# --- High-Performance Caching ---
cache = TTLCache(maxsize=1024, ttl=600)

# --- NEW: Ultra-fast endpoint for the Market Scanner ---
@app.route("/api/market-scanner")
def get_market_scanner_data():
    """
    Serves the pre-computed historical data needed by the market scanner.
    This avoids client-side timeouts by providing all data in a single request.
    """
    try:
        with open("scanner_data.json", "r") as f:
            data = json.load(f)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({"error": "Scanner data file not found. The background job may not have run yet."}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred reading scanner data: {str(e)}"}), 500

# --- Helper function for fetching OHLC data (for single-asset view) ---
def get_ohlc_data(yfinance_ticker):
    # ... (rest of the function is unchanged)
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')
    cache_key = f"{yfinance_ticker}-{period}-{interval}"
    if cache_key in cache:
        return cache[cache_key]
    asset = yf.Ticker(yfinance_ticker)
    hist_df = asset.history(period=period, interval=interval, auto_adjust=False)
    if hist_df.empty:
        return ({"error": f"Could not fetch OHLC data for '{yfinance_ticker}'."}, 404)
    hist_df.reset_index(inplace=True)
    date_col = 'Date' if 'Date' in hist_df.columns else 'Datetime'
    hist_df.rename(columns={date_col: 'Date'}, inplace=True)
    if pd.api.types.is_datetime64_any_dtype(hist_df['Date']) and hist_df['Date'].dt.tz is not None:
         hist_df['Date'] = hist_df['Date'].dt.tz_convert(None)
    hist_df['Date'] = hist_df['Date'].apply(lambda x: x.isoformat())
    data = hist_df.to_dict(orient='records')
    response = (data, 200)
    cache[cache_key] = response
    return response

# --- All other existing endpoints ---
@app.route("/")
def hello():
    return "Welcome! Finance API is live. Try: /api/market-scanner"

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/api/stock/ohlc")
# ... (this and other OHLC endpoints remain unchanged)
def get_stock_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required."}), 400
    data, status_code = get_ohlc_data(symbol.upper())
    return jsonify(data), status_code

@app.route("/api/forex/ohlc")
def get_forex_ohlc():
    pair = request.args.get('pair')
    if not pair:
        return jsonify({"error": "The 'pair' query parameter is required."}), 400
    yfinance_ticker = f"{pair.upper()}=X"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code

@app.route("/api/commodity/ohlc")
def get_commodity_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required."}), 400
    yfinance_ticker = f"{symbol.upper()}=F"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code

@app.route("/api/index/ohlc")
def get_index_ohlc():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required."}), 400
    yfinance_ticker = f"^{symbol.upper()}"
    data, status_code = get_ohlc_data(yfinance_ticker)
    return jsonify(data), status_code
