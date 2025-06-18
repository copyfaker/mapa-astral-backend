from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from skyfield.api import load, Topos
from skyfield.almanac import find_discrete, risings_and_settings
from datetime import datetime, timedelta
import pytz
import json
import os
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
CORS(app)

contador_arquivo = 'contador.json'
if not os.path.exists(contador_arquivo):
    with open(contador_arquivo, 'w') as f:
        json.dump({'total': 0}, f)

def atualizar_contador():
    with open(contador_arquivo, 'r+') as f:
        data = json.load(f)
        data['total'] += 1
        f.seek(0)
        json.dump(data, f)
        f.truncate()
        return data['total']

def carregar_contador():
    with open(contador_arquivo, 'r') as f:
        return json.load(f)

signos = [
    "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem",
    "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"
]

def get_signo(graus):
    return signos[int(graus // 30) % 12]

interpretacoes = {
    "Sol": {
        "Áries": "Personalidade intensa, iniciativa e coragem.",
        "Touro": "Busca por segurança e conforto emocional.",
        "Gêmeos": "Intelecto curioso e comunicação fluida.",
        "Câncer": "Emocional e protetor da família.",
        "Leão": "Expressivo e com senso de liderança.",
        "Virgem": "Detalhista e analítico.",
        "Libra": "Busca equilíbrio e relações harmoniosas.",
        "Escorpião": "Profundo, intenso e reservado.",
        "Sagitário": "Aventureiro e idealista.",
        "Capricórnio": "Disciplinado e focado em conquistas.",
        "Aquário": "Inovador e independente.",
        "Peixes": "Sensível, intuitivo e criativo."
    }
}

@app.route('/api/mapa', methods=['POST'])
def gerar_mapa():
    dados = request.get_json()
    nome = dados.get('nome', 'Sem nome')
    data_str = dados.get('data')  # formato dd/mm/yyyy
    hora_str = dados.get('hora')  # formato hh:mm
    cidade = dados.get('cidade')
    pais = dados.get('pais')

    if not (data_str and hora_str and cidade and pais):
        return jsonify({'erro': 'Faltando dados necessários'}), 400

    dia, mes, ano = map(int, data_str.split("/"))
    hora, minuto = map(int, hora_str.split(":"))

    # Obter coordenadas da cidade
    geo = Nominatim(user_agent="mapa-astral")
    loc = geo.geocode(f"{cidade}, {pais}")
    if not loc:
        return jsonify({'erro': 'Localização não encontrada'}), 400

    lat, lon = loc.latitude, loc.longitude
    tf = TimezoneFinder()
    tzname = tf.timezone_at(lng=lon, lat=lat)
    if not tzname:
        return jsonify({'erro': 'Fuso horário não encontrado'}), 400
    tz = pytz.timezone(tzname)

    dt_local = datetime(ano, mes, dia, hora, minuto)
    dt_local = tz.localize(dt_local)
    dt_utc = dt_local.astimezone(pytz.utc)

    ts = load.timescale()
    t = ts.from_datetime(dt_utc)

    eph = load('de421.bsp')

    planetas = {
        "Sol": eph['sun'],
        "Lua": eph['moon'],
        "Mercúrio": eph['mercury'],
        "Vênus": eph['venus'],
        "Marte": eph['mars'],
        "Júpiter": eph['jupiter barycenter'],
        "Saturno": eph['saturn barycenter'],
        "Urano": eph['uranus barycenter'],
        "Netuno": eph['neptune barycenter'],
        "Plutão": eph['pluto barycenter']
    }

    terra = eph['earth']
    resultado = []

    for nome_planeta, planeta in planetas.items():
        astrometric = terra.at(t).observe(planeta)
        ecl_lon, ecl_lat, distance = astrometric.ecliptic_latlon()
        graus = ecl_lon.degrees % 360
        signo = get_signo(graus)
        grau_signo = graus % 30
        interpretacao = interpretacoes.get(nome_planeta, {}).get(signo, "Em breve.")
        resultado.append(f"{nome_planeta}: {grau_signo:.2f}° de {signo} — {interpretacao}")

    acessos = atualizar_contador()

    return jsonify({
        'planetas': resultado,
        'total_acessos': acessos
    })

@app.route('/api/pdf', methods=['POST'])
def gerar_pdf():
    dados = request.get_json()
    nome = dados.get('nome', 'Sem nome')
    resultados = dados.get('resultados', [])

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 800, f"Mapa Astral de {nome}")

    y = 770
    for linha in resultados:
        pdf.drawString(70, y, f"- {linha}")
        y -= 20
        if y < 50:
            pdf.showPage()
            y = 800

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"MapaAstral_{nome}.pdf", mimetype='application/pdf')

@app.route('/api/contador')
def contador():
    return jsonify(carregar_contador())
    
@app.route('/')
def home():
    return "API do Mapa Astral está no ar! Use /api/mapa para enviar dados."

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
