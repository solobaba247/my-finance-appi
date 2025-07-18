# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import time

# --- INITIALIZATION ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- CONFIGURATION ---
YFINANCE_INTERVALS = {
    'Daily': '1d', '60min': '60m', '30min': '30m',
    '15min': '15m', '5min': '5m', '1min': '1m',
}
ASSET_CONFIGS = {
    'STOCKS': {'suffix': '', 'description': 'Stock market securities', 'examples': ['AAPL', 'GOOGL', 'MSFT']},
    'FOREX': {'suffix': '=X', 'description': 'Foreign exchange pairs', 'examples': ['EURUSD=X', 'GBPJPY=X']},
    'CRYPTO': {'suffix': '-USD', 'description': 'Cryptocurrency pairs', 'examples': ['BTC-USD', 'ETH-USD']},
    'COMMODITIES': {'suffix': '=F', 'description': 'Commodity futures', 'examples': ['GC=F', 'CL=F']},
    'INDICES': {'suffix': '', 'description': 'Market indices', 'examples': ['^GSPC', '^DJI', '^IXIC']},
    'ETF': {'suffix': '', 'description': 'Exchange-traded funds', 'examples': ['SPY', 'QQQ', 'GLD']},
    'BONDS': {'suffix': '', 'description': 'Treasury bonds and notes', 'examples': ['^TNX', '^IRX', '^TYX']}
}

# --- CACHING ---
# Simple in-memory cache to improve performance and avoid rate limiting.
# In a larger application, consider using a dedicated cache like Redis.
CACHE = {}
CACHE_DURATION_SECONDS = 300  # Cache data for 5 minutes

# --- HELPER FUNCTIONS ---

def get_period_for_interval(interval):
    if interval == '1d': return "2y"
    if interval in ['60m', '30m', '15m', '5m']: return "60d"
    if interval == '1m': return "7d"
    return "1y"

def format_symbol(symbol, asset_type):
    config = ASSET_CONFIGS.get(asset_type, {})
    suffix = config.get('suffix')
    if not suffix: return symbol
    if asset_type == 'FOREX' and '/' in symbol: symbol = symbol.replace('/', '')
    return f"{symbol.upper()}{suffix}" if not symbol.upper().endswith(suffix) else symbol.upper()

def _fetch_and_format_data(ticker_symbol, yf_interval):
    """
    Internal helper to fetch, cache, and format data from yfinance.
    Returns a tuple of (data, error_response). One will be None.
    """
    cache_key = f"{ticker_symbol}_{yf_interval}"
    current_time = time.time()

    if cache_key in CACHE and (current_time - CACHE[cache_key]['timestamp']) < CACHE_DURATION_SECONDS:
        return CACHE[cache_key]['data'], None

    try:
        period = get_period_for_interval(yf_interval)
        data = yf.download(tickers=ticker_symbol, period=period, interval=yf_interval, progress=False)

        if data.empty:
            return None, (jsonify({"Error Message": f"No data found for symbol {ticker_symbol}."}), 404)
        
        if data.index.tz is None: data = data.tz_localize('UTC')
        else: data = data.tz_convert('UTC')
            
        formatted_data = {
            ts.strftime('%Y-%m-%d %H:%M:%S'): {
                "1. open": str(row['Open']), "2. high": str(row['High']),
                "3. low": str(row['Low']), "4. close": str(row['Close']),
                "5. volume": str(int(row['Volume']))
            }
            for ts, row in data.iterrows() if not row.isnull().any()
        }

        CACHE[cache_key] = {'data': formatted_data, 'timestamp': current_time}
        return formatted_data, None

    except Exception as e:
        return None, (jsonify({"Error Message": f"An error occurred fetching data for {ticker_symbol}: {str(e)}"}), 500)


# --- API ENDPOINTS ---

@app.route('/')
def index():
    """Root endpoint for API discoverability and status check."""
    return jsonify({
        "message": "Welcome to My Finance API!",
        "status": "Live and Caching Enabled",
        "cache_status": {"cached_items": len(CACHE), "cache_duration_seconds": CACHE_DURATION_SECONDS},
        "endpoints": ["/get_market_data", "/get_crypto_data", "/get_forex_data", "/get_market_overview", "/get_supported_assets"]
    })

@app.route('/get_market_data')
def get_market_data():
    symbol = request.args.get('symbol')
    interval_key = request.args.get('interval', 'Daily')
    asset_type = request.args.get('assetType', 'STOCKS')

    if not symbol: return jsonify({"Error Message": "Symbol parameter is required."}), 400
    if interval_key not in YFINANCE_INTERVALS: return jsonify({"Error Message": f"Invalid interval: {interval_key}."}), 400
    if asset_type not in ASSET_CONFIGS: return jsonify({"Error Message": f"Invalid asset type: {asset_type}."}), 400

    formatted_symbol = format_symbol(symbol, asset_type)
    data, error = _fetch_and_format_data(formatted_symbol, YFINANCE_INTERVALS[interval_key])
    
    if error: return error

    return jsonify({
        f"Time Series ({interval_key})": data,
        "Meta Data": {
            "1. Information": f"{ASSET_CONFIGS[asset_type]['description']} data",
            "2. Symbol": formatted_symbol, "3. Interval": interval_key
        }
    })

@app.route('/get_crypto_data')
def get_crypto_data():
    symbol = request.args.get('symbol')
    interval_key = request.args.get('interval', 'Daily')
    vs_currency = request.args.get('vs_currency', 'USD')
    
    if not symbol: return jsonify({"Error Message": "Crypto symbol parameter is required."}), 400
    if interval_key not in YFINANCE_INTERVALS: return jsonify({"Error Message": f"Invalid interval: {interval_key}"}), 400

    crypto_symbol = f"{symbol.upper()}-{vs_currency.upper()}"
    data, error = _fetch_and_format_data(crypto_symbol, YFINANCE_INTERVALS[interval_key])
    
    if error: return error

    return jsonify({
        f"Crypto Time Series ({interval_key})": data,
        "Meta Data": {"1. Symbol": crypto_symbol, "2. Interval": interval_key}
    })

@app.route('/get_forex_data')
def get_forex_data():
    base = request.args.get('base_currency')
    quote = request.args.get('quote_currency') 
    interval_key = request.args.get('interval', 'Daily')
    
    if not base or not quote: return jsonify({"Error Message": "base_currency and quote_currency are required."}), 400
    if interval_key not in YFINANCE_INTERVALS: return jsonify({"Error Message": f"Invalid interval: {interval_key}"}), 400

    forex_symbol = f"{base.upper()}{quote.upper()}=X"
    data, error = _fetch_and_format_data(forex_symbol, YFINANCE_INTERVALS[interval_key])
    
    if error: return error

    return jsonify({
        f"Forex Time Series ({interval_key})": data,
        "Meta Data": {"1. Symbol": forex_symbol, "2. Interval": interval_key}
    })

@app.route('/get_market_overview')
def get_market_overview():
    cache_key = "market_overview"
    current_time = time.time()
    if cache_key in CACHE and (current_time - CACHE[cache_key]['timestamp']) < CACHE_DURATION_SECONDS:
        return jsonify(CACHE[cache_key]['data'])

    try:
        major_indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX']
        tickers = yf.Tickers(' '.join(major_indices))
        overview_data = {}
        
        for symbol in major_indices:
            info = tickers.tickers[symbol].info
            hist = tickers.tickers[symbol].history(period='2d', progress=False)
            if not hist.empty and len(hist) > 1:
                change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                change_percent = (change / hist['Close'].iloc[-2]) * 100
                overview_data[symbol] = {
                    'name': info.get('longName', symbol),
                    'price': round(hist['Close'].iloc[-1], 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2)
                }
        
        response_data = {"market_overview": overview_data}
        CACHE[cache_key] = {'data': response_data, 'timestamp': current_time}
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"Error Message": f"An error occurred fetching market overview: {str(e)}"}), 500

@app.route('/get_supported_assets')
def get_supported_assets():
    """Returns static configuration data, no caching needed."""
    return jsonify({
        "supported_assets": ASSET_CONFIGS,
        "supported_intervals": list(YFINANCE_INTERVALS.keys())
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
