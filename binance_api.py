#binance_api.py
import requests
import logging

logger = logging.getLogger(__name__)

def get_current_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        price_info = {
            "symbol": symbol,
            "last_price": float(data["lastPrice"]),
            "price_change_percent": float(data["priceChangePercent"]),
            "high_price": float(data["highPrice"]),
            "volume": float(data["volume"])
        }

        return {"success": True, "data": price_info}

    except Exception as e:
        logger.error(e)
        return {"success": False, "error": e}

if __name__ == "__main__":
    # Тест
    result = get_current_price("BTCUSDT")
    print(result)