# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

# Initialize the Flask app
app = Flask(__name__)
# Enable CORS to allow requests from your Blogspot domain
CORS(app)

# Map our app's intervals to yfinance intervals
YFINANCE_INTERVALS = {
    'Daily': '1d',
    '60min': '60m',
    '30min': '30m',
    '15min': '15m',
    '5min': '5m',
    '1min': '1m',  # Added 1-minute interval
}

# Asset type configurations
ASSET_CONFIGS = {
    'STOCKS': {
        'suffix': '',
        'description': 'Stock market securities',
        'examples': ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    },
    'FOREX': {
        'suffix': '=X',
        'description': 'Foreign exchange pairs',
        'examples': ['EURUSD=X', 'GBPJPY=X', 'USDJPY=X']
    },
    'CRYPTO': {
        'suffix': '-USD',
        'description': 'Cryptocurrency pairs',
        'examples': ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD']
    },
    'COMMODITIES': {
        'suffix': '=F',
        'description': 'Commodity futures',
        'examples': ['GC=F', 'CL=F', 'NG=F', 'ZC=F']  # Gold, Oil, Natural Gas, Corn
    },
    'INDICES': {
        'suffix': '',
        'description': 'Market indices',
        'examples': ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow Jones, NASDAQ, Russell 2000
    },
    'ETF': {
        'suffix': '',
        'description': 'Exchange-traded funds',
        'examples': ['SPY', 'QQQ', 'IWM', 'GLD']
    },
    'BONDS': {
        'suffix': '',
        'description': 'Treasury bonds and notes',
        'examples': ['^TNX', '^IRX', '^FVX', '^TYX']  # 10Y, 3M, 5Y, 30Y Treasury
    }
}

def format_symbol(symbol, asset_type):
    """Format symbol based on asset type"""
    if asset_type == 'FOREX':
        # Convert USD/EUR format to USDEUR=X
        if '/' in symbol:
            symbol = symbol.replace('/', '')
        return f"{symbol}=X"
    elif asset_type == 'CRYPTO':
        if not symbol.endswith('-USD'):
            return f"{symbol}-USD"
        return symbol
    elif asset_type == 'COMMODITIES':
        if not symbol.endswith('=F'):
            return f"{symbol}=F"
        return symbol
    else:
        return symbol

def get_period_for_interval(interval):
    """Get appropriate period based on interval"""
    if interval == '1d':
        return "2y"  # 2 years for daily
    elif interval in ['60m', '30m']:
        return "60d"  # 60 days for hourly/30min
    elif interval in ['15m', '5m']:
        return "60d"  # 60 days for 15min/5min
    elif interval == '1m':
        return "7d"   # 7 days for 1-minute (yfinance limitation)
    else:
        return "1y"

# Main API endpoint
@app.route('/get_market_data')
def get_market_data():
    symbol = request.args.get('symbol')
    interval_key = request.args.get('interval', 'Daily')
    asset_type = request.args.get('assetType', 'STOCKS')

    if not symbol:
        return jsonify({"Error Message": "Stock symbol parameter is required."}), 400

    yf_interval = YFINANCE_INTERVALS.get(interval_key)
    if not yf_interval:
        return jsonify({"Error Message": f"Invalid interval: {interval_key}. Valid intervals: {list(YFINANCE_INTERVALS.keys())}"}), 400
    
    if asset_type not in ASSET_CONFIGS:
        return jsonify({"Error Message": f"Invalid asset type: {asset_type}. Valid types: {list(ASSET_CONFIGS.keys())}"}), 400

    # Format symbol based on asset type
    formatted_symbol = format_symbol(symbol, asset_type)
    
    try:
        period = get_period_for_interval(yf_interval)
        
        data = yf.download(tickers=formatted_symbol, period=period, interval=yf_interval)

        if data.empty:
            return jsonify({"Error Message": f"No data found for symbol {formatted_symbol} with interval {yf_interval}. It might be a delisted ticker or an invalid interval for this period."}), 404

        # Handle timezone
        if data.index.tz is None:
            data = data.tz_localize('UTC')
        else:
            data = data.tz_convert('UTC')

        time_series_key = f"Time Series ({interval_key})"
        
        formatted_data = {}
        for timestamp, row in data.iterrows():
            date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            formatted_data[date_str] = {
                "1. open": str(row['Open']),
                "2. high": str(row['High']),
                "3. low": str(row['Low']),
                "4. close": str(row['Close']),
                "5. volume": str(row['Volume'])
            }
            
        response_json = {
            time_series_key: formatted_data,
            "Meta Data": {
                "1. Information": f"{ASSET_CONFIGS[asset_type]['description']} data from yfinance",
                "2. Symbol": formatted_symbol,
                "3. Asset Type": asset_type,
                "4. Interval": interval_key,
                "5. Period": period
            }
        }
        
        return jsonify(response_json)

    except Exception as e:
        return jsonify({"Error Message": f"An error occurred: {str(e)}"}), 500

# New endpoint: Get supported asset types and their examples
@app.route('/get_supported_assets')
def get_supported_assets():
    """Return information about supported asset types"""
    return jsonify({
        "supported_assets": ASSET_CONFIGS,
        "supported_intervals": list(YFINANCE_INTERVALS.keys())
    })

# New endpoint: Get crypto market data (specialized endpoint)
@app.route('/get_crypto_data')
def get_crypto_data():
    """Specialized endpoint for cryptocurrency data"""
    symbol = request.args.get('symbol')
    interval_key = request.args.get('interval', 'Daily')
    vs_currency = request.args.get('vs_currency', 'USD')  # Default to USD
    
    if not symbol:
        return jsonify({"Error Message": "Crypto symbol parameter is required."}), 400
    
    # Format crypto symbol
    crypto_symbol = f"{symbol.upper()}-{vs_currency.upper()}"
    
    yf_interval = YFINANCE_INTERVALS.get(interval_key)
    if not yf_interval:
        return jsonify({"Error Message": f"Invalid interval: {interval_key}"}), 400
    
    try:
        period = get_period_for_interval(yf_interval)
        data = yf.download(tickers=crypto_symbol, period=period, interval=yf_interval)
        
        if data.empty:
            return jsonify({"Error Message": f"No data found for {crypto_symbol}"}), 404
        
        # Handle timezone
        if data.index.tz is None:
            data = data.tz_localize('UTC')
        else:
            data = data.tz_convert('UTC')
        
        formatted_data = {}
        for timestamp, row in data.iterrows():
            date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            formatted_data[date_str] = {
                "1. open": str(row['Open']),
                "2. high": str(row['High']),
                "3. low": str(row['Low']),
                "4. close": str(row['Close']),
                "5. volume": str(row['Volume'])
            }
        
        return jsonify({
            f"Crypto Time Series ({interval_key})": formatted_data,
            "Meta Data": {
                "1. Information": "Cryptocurrency data from yfinance",
                "2. Symbol": crypto_symbol,
                "3. Base Currency": symbol.upper(),
                "4. Quote Currency": vs_currency.upper(),
                "5. Interval": interval_key
            }
        })
    
    except Exception as e:
        return jsonify({"Error Message": f"An error occurred: {str(e)}"}), 500

# New endpoint: Get forex data (specialized endpoint)
@app.route('/get_forex_data')
def get_forex_data():
    """Specialized endpoint for forex data"""
    base_currency = request.args.get('base_currency')
    quote_currency = request.args.get('quote_currency') 
    interval_key = request.args.get('interval', 'Daily')
    
    if not base_currency or not quote_currency:
        return jsonify({"Error Message": "Both base_currency and quote_currency parameters are required."}), 400
    
    forex_symbol = f"{base_currency.upper()}{quote_currency.upper()}=X"
    
    yf_interval = YFINANCE_INTERVALS.get(interval_key)
    if not yf_interval:
        return jsonify({"Error Message": f"Invalid interval: {interval_key}"}), 400
    
    try:
        period = get_period_for_interval(yf_interval)
        data = yf.download(tickers=forex_symbol, period=period, interval=yf_interval)
        
        if data.empty:
            return jsonify({"Error Message": f"No data found for {forex_symbol}"}), 404
        
        # Handle timezone
        if data.index.tz is None:
            data = data.tz_localize('UTC')
        else:
            data = data.tz_convert('UTC')
        
        formatted_data = {}
        for timestamp, row in data.iterrows():
            date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            formatted_data[date_str] = {
                "1. open": str(row['Open']),
                "2. high": str(row['High']),
                "3. low": str(row['Low']),
                "4. close": str(row['Close']),
                "5. volume": str(row['Volume'])
            }
        
        return jsonify({
            f"Forex Time Series ({interval_key})": formatted_data,
            "Meta Data": {
                "1. Information": "Forex data from yfinance",
                "2. Symbol": forex_symbol,
                "3. Base Currency": base_currency.upper(),
                "4. Quote Currency": quote_currency.upper(),
                "5. Interval": interval_key
            }
        })
    
    except Exception as e:
        return jsonify({"Error Message": f"An error occurred: {str(e)}"}), 500

# New endpoint: Get market overview
@app.route('/get_market_overview')
def get_market_overview():
    """Get overview of major market indices"""
    major_indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX']
    overview_data = {}
    
    try:
        for symbol in major_indices:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='2d')
            
            if not hist.empty:
                latest = hist.iloc[-1]
                previous = hist.iloc[-2] if len(hist) > 1 else latest
                
                change = latest['Close'] - previous['Close']
                change_percent = (change / previous['Close']) * 100
                
                overview_data[symbol] = {
                    'name': info.get('longName', symbol),
                    'price': round(latest['Close'], 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': int(latest['Volume'])
                }
        
        return jsonify({
            "market_overview": overview_data,
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({"Error Message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
