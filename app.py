# This is our main application file

from flask import Flask, jsonify
import yfinance as yf

# Create the app
app = Flask(__name__)

# A simple hello world route
@app.route("/")
def hello():
    return "Welcome! Try /api/stock/AAPL or /api/stock/GOOGL"

# The main route to get stock data
@app.route("/api/stock/<string:ticker_symbol>")
def get_stock_info(ticker_symbol):
    
    # Use the yfinance library to get the stock object
    stock = yf.Ticker(ticker_symbol)
    
    # Check if the stock exists by checking its 'info'
    if not stock.history(period="1d").empty:
        # If it exists, get the data
        info = stock.info
        data = {
            "companyName": info.get('longName'),
            "symbol": info.get('symbol'),
            "currentPrice": info.get('currentPrice'),
        }
        return jsonify(data)
    else:
        # If it doesn't exist, return an error
        return jsonify({"error": "Stock symbol not found"}), 404
