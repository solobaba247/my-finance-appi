
from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome! API is live. Try /api/stock/AAPL, /api/forex/EURUSD, or /api/stock/MSFT/ohlc?period=1mo"

# --- Stock Endpoint (No changes here) ---
@app.route("/api/stock/<string:ticker_symbol>")
def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    if stock.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Stock symbol '{ticker_symbol}' not found or data is unavailable."}), 404
    else:
        info = stock.info
        data = {
            "companyName": info.get('longName'),
            "symbol": info.get('symbol'),
            "currentPrice": info.get('currentPrice'),
            "marketCap": info.get('marketCap')
        }
        return jsonify(data)

# --- Forex Endpoint (No changes here) ---
@app.route("/api/forex/<string:pair>")
def get_forex_data(pair):
    forex_ticker = f"{pair.upper()}=X"
    currency = yf.Ticker(forex_ticker)
    if currency.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Forex pair '{pair}' not found or data is unavailable."}), 404
    else:
        info = currency.info
        data = {
            "pairName": info.get('shortName'),
            "symbol": info.get('symbol'),
            "currentPrice": info.get('regularMarketPrice'),
            "dayHigh": info.get('dayHigh'),
            "dayLow": info.get('dayLow')
        }
        return jsonify(data)

# --- NEW: OHLC Endpoint ---
@app.route("/api/stock/<string:ticker_symbol>/ohlc")
def get_stock_ohlc(ticker_symbol):
    # Get query parameters for period and interval with sensible defaults
    period = request.args.get('period', '1mo') # Default to 1 month
    interval = request.args.get('interval', '1d') # Default to 1 day

    stock = yf.Ticker(ticker_symbol)

    # Fetch historical market data
    # We set auto_adjust=False to get the classic OHLC columns
    hist_df = stock.history(period=period, interval=interval, auto_adjust=False)

    # Check if the DataFrame is empty (happens for invalid tickers or periods)
    if hist_df.empty:
        return jsonify({
            "error": f"Could not fetch OHLC data for '{ticker_symbol}'. Check ticker, period, or interval."
        }), 404

    # The index is a Datetime object. We need to reset it to be a column
    # and then format it to a string so it can be converted to JSON.
    hist_df.reset_index(inplace=True)
    hist_df['Date'] = hist_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convert the DataFrame to a list of dictionaries (records)
    data = hist_df.to_dict(orient='records')
    return jsonify(data)
