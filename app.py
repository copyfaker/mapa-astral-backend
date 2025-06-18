# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

app = Flask(__name__)
CORS(app)

contador = 0

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    return tz_name

def generate_real_chart(data, hora, cidade, pais):
    geolocator = Nominatim(user_agent="mapa-astral-app")
    location = geolocator.geocode(f"{cidade}, {pais}")

    if not location:
        raise ValueError("Localização não encontrada")

    lat, lon = location.latitude, location.longitude
    tz_name = get_timezone(lat, lon)
    tz = pytz.timezone(tz_name)

    dt_local = tz.localize(pytz.datetime.datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M"))
    dt_utc = dt_local.astimezone(pytz.utc)

    date_str = dt_utc.strftime("%Y/%m/%d")
    time_str = dt_utc.strftime("%H:%M")

    pos = GeoPos(str(lat), str(lon), cidade)
    date = Datetime(date_str, time_str, "+00:00")
    chart = Chart(date, pos)

    planetas = [const.SUN, const.MOON, const.ASC, const.MERCURY, const.VENUS, const.MARS,
                const.JUPITER, const.SATURN]

    resultado = {
        "planetas": [f"{planet} em {chart.get(planet).sign} na Casa {chart.get(planet).house}" for planet in planetas],
        "signos": [
            f"Signo Solar: {chart.get(const.SUN).sign}",
            f"Signo Lunar: {chart.get(const.MOON).sign}",
            f"Ascendente: {chart.get(const.ASC).sign}"
        ],
        "casas": [
            f"Casa {i+1}: {chart.houses[i].sign}" for i in range(12)
        ],
        "aspectos": []  # pode ser preenchido depois com aspectos reais
    }
    return resultado

@app.route("/api/mapa", methods=["POST"])
def calcular_mapa():
    data = request.get_json()
    try:
        resultado = generate_real_chart(
            data['data'],
            data['hora'],
            data['cidade'],
            data['pais']
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route("/api/contador", methods=["GET"])
def get_acessos():
    global contador
    contador += 1
    return jsonify({"total": contador})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
