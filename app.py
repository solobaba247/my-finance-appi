
from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome! API is live. Try /api/stock/AAPL/ohlc or /api/forex/EURUSD/ohlc?period=1d&interval=1h"

# --- Stock Info Endpoint ---
@app.route("/api/stock/<string:ticker_symbol>")
def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    if stock.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Stock symbol '{ticker_symbol}' not found or data is unavailable."}), 404
    else:
        info = stock.info
        data = { "companyName": info.get('longName'), "symbol": info.get('symbol'), "currentPrice": info.get('currentPrice'), "marketCap": info.get('marketCap') }
        return jsonify(data)

# --- Forex Info Endpoint ---
@app.route("/api/forex/<string:pair>")
def get_forex_data(pair):
    forex_ticker = f"{pair.upper()}=X"
    currency = yf.Ticker(forex_ticker)
    if currency.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Forex pair '{pair}' not found or data is unavailable."}), 404
    else:
        info = currency.info
        data = { "pairName": info.get('shortName'), "symbol": info.get('symbol'), "currentPrice": info.get('regularMarketPrice'), "dayHigh": info.get('dayHigh'), "dayLow": info.get('dayLow') }
        return jsonify(data)

# --- Stock OHLC Endpoint ---
@app.route("/api/stock/<string:ticker_symbol>/ohlc")
def get_stock_ohlc(ticker_symbol):
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')
    stock = yf.Ticker(ticker_symbol)
    hist_df = stock.history(period=period, interval=interval, auto_adjust=False)
    if hist_df.empty:
        return jsonify({"error": f"Could not fetch OHLC data for '{ticker_symbol}'. Check ticker, period, or interval."}), 404
    hist_df.reset_index(inplace=True)
    if 'Datetime' in hist_df.columns:
        hist_df.rename(columns={'Datetime': 'Date'}, inplace=True)
    hist_df['Date'] = hist_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    data = hist_df.to_dict(orient='records')
    return jsonify(data)

# --- NEW: Forex OHLC Endpoint ---
@app.route("/api/forex/<string:pair>/ohlc")
def get_forex_ohlc(pair):
    period = request.args.get('period', '1d')
    interval = request.args.get('interval', '1h')
    forex_ticker = f"{pair.upper()}=X"
    currency = yf.Ticker(forex_ticker)
    hist_df = currency.history(period=period, interval=interval, auto_adjust=False)
    if hist_df.empty:
        return jsonify({"error": f"Could not fetch OHLC data for Forex pair '{pair}'. Check pair, period, or interval."}), 404
    hist_df.reset_index(inplace=True)
    if 'Datetime' in hist_df.columns:
        hist_df.rename(columns={'Datetime': 'Date'}, inplace=True)
    hist_df['Date'] = hist_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    data = hist_df.to_dict(orient='records')
    return jsonify(data)
