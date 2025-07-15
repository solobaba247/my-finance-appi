# app.py (V3: Supports Stocks, Forex, Commodities, and Indices)

from flask import Flask, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# --- Helper function for fetching and formatting OHLC data ---
# This reduces code duplication, as the logic is the same for all asset types.
def get_ohlc_data(yfinance_ticker):
    """
    Fetches, validates, and formats OHLC data for a given yfinance ticker.
    Returns a tuple of (data, status_code).
    """
    # Get period and interval from query parameters, with default values
    period = request.args.get('period', '1mo')
    interval = request.args.get('interval', '1d')

    # Fetch historical data
    asset = yf.Ticker(yfinance_ticker)
    hist_df = asset.history(period=period, interval=interval, auto_adjust=False)

    # Validate that we received data
    if hist_df.empty:
        error_msg = f"Could not fetch OHLC data for '{yfinance_ticker}'. Check symbol, period ('{period}'), or interval ('{interval}')."
        return {"error": error_msg}, 404
    
    # Format the data for JSON response
    hist_df.reset_index(inplace=True)
    # The date column can be 'Date' or 'Datetime', we handle both
    date_col = 'Date' if 'Date' in hist_df.columns else 'Datetime'
    hist_df.rename(columns={date_col: 'Date'}, inplace=True)
    hist_df['Date'] = hist_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    
    data = hist_df.to_dict(orient='records')
    return data, 200


@app.route("/")
def hello():
    return "Welcome! Finance API is live. Try: /api/stock?symbol=AAPL or /api/commodity/ohlc?symbol=GC"

# =================================================================
#  INFO ENDPOINTS
# =================================================================

@app.route("/api/stock")
def get_stock_info():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/stock?symbol=AAPL"}), 400
    
    stock = yf.Ticker(symbol.upper())
    if stock.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Stock symbol '{symbol}' not found or data is unavailable."}), 404
    
    info = stock.info
    data = { "companyName": info.get('longName'), "symbol": info.get('symbol'), "currentPrice": info.get('currentPrice'), "marketCap": info.get('marketCap') }
    return jsonify(data)

@app.route("/api/forex")
def get_forex_info():
    pair = request.args.get('pair')
    if not pair:
        return jsonify({"error": "The 'pair' query parameter is required. Example: /api/forex?pair=EURUSD"}), 400

    yfinance_ticker = f"{pair.upper()}=X"
    currency = yf.Ticker(yfinance_ticker)
    if currency.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Forex pair '{pair}' not found or data is unavailable."}), 404
    
    info = currency.info
    data = { "pairName": info.get('shortName'), "symbol": info.get('symbol'), "currentPrice": info.get('regularMarketPrice'), "dayHigh": info.get('dayHigh'), "dayLow": info.get('dayLow') }
    return jsonify(data)

@app.route("/api/commodity")
def get_commodity_info():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/commodity?symbol=GC (Gold)"}), 400
    
    # Commodity futures on yfinance often end in '=F'
    yfinance_ticker = f"{symbol.upper()}=F"
    commodity = yf.Ticker(yfinance_ticker)
    if commodity.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Commodity symbol '{symbol}' not found or data is unavailable."}), 404
        
    info = commodity.info
    data = { "name": info.get('shortName'), "symbol": info.get('symbol'), "currentPrice": info.get('regularMarketPrice'), "exchange": info.get('exchange') }
    return jsonify(data)

@app.route("/api/index")
def get_index_info():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "The 'symbol' query parameter is required. Example: /api/index?symbol=GSPC (S&P 500)"}), 400

    # Major indices on yfinance often start with '^'
    yfinance_ticker = f"^{symbol.upper()}"
    index = yf.Ticker(yfinance_ticker)
    if index.info.get('regularMarketPrice') is None:
        return jsonify({"error": f"Index symbol '{symbol}' not found or data is unavailable."}), 404

    info = index.info
    data = { "name": info.get('shortName'), "symbol": info.get('symbol'), "currentPrice": info.get('regularMarketPrice'), "previousClose": info.get('previousClose') }
    return jsonify(data)


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
