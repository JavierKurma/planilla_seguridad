from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__, static_folder="static")

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Yaris.2017@localhost:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(50))
    obra = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    registro = db.Column(db.String(50))
    observaciones = db.Column(db.Text)

EXCEL_FILE = "planilla.xlsx"

@app.route("/")
def home():
    return send_from_directory("static", "index.html")


from datetime import datetime

@app.route("/guardar", methods=["POST"])
def guardar():

    data = request.form.to_dict(flat=False)

    # helper para sacar primer valor
    def get_value(key):
        return data.get(key, [""])[0]

    # -------------------------
    # REGISTRO MULTIPLE (IV+C+PT)
    # -------------------------
    registros = data.get("registro", [])
    registro_texto = "+".join(registros)

    # -------------------------
    # PROCESAR ARCHIVOS
    # -------------------------
    archivos = request.files.getlist("archivos")

    nombres_archivos = []

    if archivos:
        os.makedirs("uploads", exist_ok=True)

        for archivo in archivos:
            if archivo and archivo.filename != "":
                nombre = f"{datetime.now().timestamp()}_{archivo.filename}"
                archivo.save(os.path.join("uploads", nombre))
                nombres_archivos.append(nombre)

    # convertir lista a texto
    archivos_texto = " | ".join(nombres_archivos)
    # -------------------------
    # PROCESAR OBSERVACIONES
    # -------------------------
    observaciones_texto = ""
    ca_total = 0
    ao_total = 0

    i = 0
    while f"obs_{i}" in data:
        obs = get_value(f"obs_{i}")
        rec = get_value(f"rec_{i}")
        plazo = get_value(f"plazo_{i}")
        resp = get_value(f"resp_{i}")
        ca = int(get_value(f"ca_{i}") or 0)
        ao = int(get_value(f"ao_{i}") or 0)

        ca_total += ca
        ao_total += ao

        observaciones_texto += f"""
{i+1}) Observación: {obs}
   Recomendación: {rec}
   Plazo: {plazo}
   Responsable: {resp}
   CA: {ca} | AO: {ao}
"""
        i += 1

    # -------------------------
    # CALCULAR HORAS
    # -------------------------
    inicio_str = get_value("inicio")
    final_str = get_value("final")

    if inicio_str and final_str:
        inicio = datetime.strptime(inicio_str, "%H:%M")
        final = datetime.strptime(final_str, "%H:%M")
        horas = (final - inicio).seconds / 3600
    else:
        horas = 0

    # -------------------------
    # ARMAR REGISTRO FINAL
    # -------------------------
    registro = {
        "fecha": get_value("fecha"),
        "obra": get_value("obra"),
        "empresa": get_value("empresa"),
        "registro": registro_texto,
        "ACTIVIDADES_OBS_ANT": get_value("actividades"),
        "ASPECTOS_POSITIVOS": get_value("aspectos"),
        "OBSERVACIONES": observaciones_texto,
        "CA_total": ca_total,
        "AO_total": ao_total,
        "auditor": get_value("auditor"),
        "inicio": inicio_str,
        "final": final_str,
        "horas": horas,
        "pdf": archivos_texto,
        "valor_hora": "",
        "honorarios": "",
        "gastos": "",
        "pagos": "",
        "observaciones_admin": "",
        "visitas": ""
    }

    nuevo = Registro(
        fecha=get_value("fecha"),
        obra=get_value("obra"),
        empresa=get_value("empresa"),
        registro=registro_texto,
        observaciones=observaciones_texto
    )
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({"mensaje": "Guardado correctamente"})
"""
@app.route("/registros")
def ver_registros():
    registros = Registro.query.all()

    resultado = []
    for r in registros:
        resultado.append({
            "id": r.id,
            "fecha": r.fecha,
            "obra": r.obra,
            "empresa": r.empresa,
            "registro": r.registro,
            "observaciones": r.observaciones
        })

    return jsonify(resultado)
"""
@app.route("/panel")
def panel():
    clave = request.args.get("key")

    if clave != "Estambul2023":
        return "No autorizado", 403

    registros = Registro.query.all()

    html = "<h2>Registros</h2>"

    for r in registros:
        html += f"<div>{r.id} - {r.obra}</div>"

    return html

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)