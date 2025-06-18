from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pyswisseph as swe
import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import os
import json
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
CORS(app)

swe.set_ephe_path('.')
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
    return signos[int(graus / 30)]

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
    nome = dados['nome']
    data = dados['data']
    hora = dados['hora']
    cidade = dados['cidade']
    pais = dados['pais']

    dia, mes, ano = map(int, data.split("/"))
    hora, minuto = map(int, hora.split(":"))

    geo = Nominatim(user_agent="mapa-astral")
    loc = geo.geocode(f"{cidade}, {pais}")
    if not loc:
        return jsonify({'erro': 'Localização não encontrada'}), 400

    lat, lon = loc.latitude, loc.longitude
    tf = TimezoneFinder()
    tz = pytz.timezone(tf.timezone_at(lng=lon, lat=lat))
    dt_local = datetime.datetime(ano, mes, dia, hora, minuto)
    dt_utc = dt_local.astimezone(pytz.utc)

    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                    dt_utc.hour + dt_utc.minute / 60)

    planetas = {
        "Sol": swe.SUN,
        "Lua": swe.MOON,
        "Mercúrio": swe.MERCURY,
        "Vênus": swe.VENUS,
        "Marte": swe.MARS,
        "Júpiter": swe.JUPITER,
        "Saturno": swe.SATURN,
        "Urano": swe.URANUS,
        "Netuno": swe.NEPTUNE,
        "Plutão": swe.PLUTO
    }

    resultado = []
    for nome_planeta, cod in planetas.items():
        pos, _ = swe.calc_ut(jd, cod)
        signo = get_signo(pos[0])
        grau = pos[0] % 30
        interpretacao = interpretacoes.get(nome_planeta, {}).get(signo, "Em breve.")
        resultado.append(f"{nome_planeta}: {grau:.2f}° de {signo} — {interpretacao}")

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

if __name__ == '__main__':
    app.run(debug=True)
