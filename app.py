
from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome! API is live. Try /api/stock/AAPL or /api/forex/EURUSD"

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

# --- NEW: Forex Endpoint ---
@app.route("/api/forex/<string:pair>")
def get_forex_data(pair):
    # We must add '=X' to the end for yfinance to recognize it as a currency pair
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
