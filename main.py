#VT
import requests
import time
from flask import Flask

WEBHOOK_URL = "https://hook.eu2.make.com/m968jyx96moktmbhvkfb2f41jnmtd3zu"

app = Flask(__name__)

def get_price_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "1"  # CoinGecko nos da precios cada pocos minutos sin poner 'interval'
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "prices" not in data or "total_volumes" not in data:
        raise ValueError(f"CoinGecko no devolvió datos válidos: {data}")

    # Últimos 15 valores (aprox. 15-30 min según disponibilidad)
    prices = [p[1] for p in data["prices"][-15:]]
    volumes = [v[1] for v in data["total_volumes"][-15:]]
    return prices, volumes

def get_price_bingx():
    url = "https://open-api.bingx.com/openApi/spot/v1/ticker/price"
    params = {"symbol": "BTC-USDT"}
    response = requests.get(url, params=params)

    print(f"🟡 Código HTTP: {response.status_code}")
    print(f"🟡 Respuesta de BingX: {response.text}")  # Añadido para ver qué devuelve realmente

    data = response.json()

    if data.get("code") != 0 or "price" not in data.get("data", {}):
        raise ValueError(f"BingX no devolvió datos válidos: {data}")

    return float(data["data"]["price"])

def calculate_rsi(prices):
    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-delta)
    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 100
    return round(rsi, 2)

@app.route("/")
def run_bot():
    try:
        prices, volumes = get_price_data()
        bingx_price = get_price_bingx()
        rsi = calculate_rsi(prices)
        trend = "alcista" if prices[-1] > prices[0] else "bajista"
        payload = {
            # "precio": round(prices[-1], 2), # Precio CoinGecko
            "precio": round(bingx_price, 2),   # Precio de BingX
            "rsi": rsi,
            "volumen": round(volumes[-1], 2),
            "tendencia": trend
        }
        requests.post(WEBHOOK_URL, json=payload)
        print(f"✅ Enviado a webhook: {payload}")
        return "Señal enviada correctamente", 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error interno", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
