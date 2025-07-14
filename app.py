
from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome! My Finance API is live. Try /api/stock/AAPL"

@app.route("/api/stock/<string:ticker_symbol>")
def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    
    # A more reliable check for a valid ticker
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
