import requests
from flask import Flask

WEBHOOK_URL = "https://hook.eu2.make.com/m968jyx96moktmbhvkfb2f41jnmtd3zu"

app = Flask(__name__)

def get_bingx_klines():
    url = "https://open-api.bingx.com/openApi/swap/v3/quote/klines"
    params = {
        "symbol": "BTC-USDT",
        "interval": "1m",
        "limit": 15
    }
    response = requests.get(url, params=params)
    data = response.json()

    print("🟦 Respuesta completa Klines:", data)

    try:
        klines = data["data"]
        if not klines:
            print("❌ BingX devolvió lista vacía de klines.")
            return [], []

        closes = [float(k["close"]) for k in klines]
        volumes = [float(k["volume"]) for k in klines]
        return closes, volumes
    except (KeyError, TypeError, IndexError) as e:
        raise ValueError(f"BingX no devolvió datos válidos: {data}")

def get_price_bingx():
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/price?symbol=BTC-USDT"
    response = requests.get(url)
    data = response.json()

    print("🔎 Respuesta cruda de BingX:", response.text)

    try:
        return float(data["data"]["price"])
    except (KeyError, TypeError):
        try:
            return float(data["data"][0]["trades"][0]["price"])
        except (KeyError, IndexError, TypeError):
            raise ValueError(f"No se pudo extraer el precio de BingX: {data}")

def calculate_rsi(prices):
    print("📈 Precios recibidos para RSI:", prices)

    if not prices or len(prices) < 2:
        print("⚠️ No hay suficientes precios para calcular RSI.")
        return 50  # Neutral

    gains = []
    losses = []

    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
            losses.append(0)
        elif delta < 0:
            gains.append(0)
            losses.append(-delta)
        else:
            gains.append(0)
            losses.append(0)

    total_points = len(gains)
    if total_points == 0:
        return 50

    avg_gain = sum(gains) / total_points
    avg_loss = sum(losses) / total_points

    print("📊 avg_gain:", avg_gain, "avg_loss:", avg_loss)

    if avg_loss == 0:
        if avg_gain == 0:
            return 50  # sin movimiento
        return 100  # solo subidas

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def detect_trend(prices):
    if not prices or len(prices) < 3:
        print("⚠️ No hay suficientes precios para detectar tendencia.")
        return "desconocida"

    short_ma = sum(prices[-3:]) / 3
    long_ma = sum(prices) / len(prices)

    if short_ma > long_ma:
        return "alcista"
    elif short_ma < long_ma:
        return "bajista"
    else:
        return "lateral"

@app.route("/")
def run_bot():
    try:
        prices, volumes = get_bingx_klines()
        bingx_price = get_price_bingx()
        rsi = calculate_rsi(prices)
        trend = detect_trend(prices)

        payload = {
            "precio": round(bingx_price, 2),
            "rsi": rsi,
            "volumen": round(volumes[-1], 2) if volumes else 0.0,
            "tendencia": trend
        }

        print("📦 Payload:", payload)
        requests.post(WEBHOOK_URL, json=payload)
        return "✅ Señal enviada correctamente", 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error interno: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
