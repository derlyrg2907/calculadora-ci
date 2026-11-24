import os
import time

import psycopg2
from flask import Flask, jsonify, request

from calculadora import dividir, multiplicar, potencia, restar, sumar

app = Flask(__name__)

OPERACIONES = {
    "sumar": sumar,
    "restar": restar,
    "multiplicar": multiplicar,
    "dividir": dividir,
    "potencia": potencia,
}


def conectar():
    # DB_HOST es el NOMBRE DEL SERVICIO en docker-compose ("db"), no localhost
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def crear_tabla():
    for intento in range(10):
        try:
            with conectar() as conn, conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS operaciones ("
                    "id SERIAL PRIMARY KEY, operacion TEXT, a REAL, b REAL, "
                    "resultado REAL, creado TIMESTAMP DEFAULT NOW())"
                )
            return
        except psycopg2.OperationalError:
            print(f"Esperando la base de datos (intento {intento + 1})...", flush=True)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar con la base de datos")


@app.get("/salud")
def salud():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
    return jsonify(estado="ok", base_de_datos=os.environ["DB_HOST"], version=version)


@app.post("/operaciones")
def guardar_operacion():
    datos = request.get_json()
    nombre = datos["operacion"]
    if nombre not in OPERACIONES:
        return jsonify(error=f"Operacion no valida: {nombre}"), 400
    a, b = float(datos["a"]), float(datos["b"])
    resultado = OPERACIONES[nombre](a, b)
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO operaciones (operacion, a, b, resultado) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (nombre, a, b, resultado),
        )
        nuevo_id = cur.fetchone()[0]
    return jsonify(id=nuevo_id, operacion=nombre, a=a, b=b, resultado=resultado), 201


@app.get("/operaciones")
def listar_operaciones():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, operacion, a, b, resultado FROM operaciones ORDER BY id")
        filas = cur.fetchall()
    return jsonify([
        {"id": f[0], "operacion": f[1], "a": f[2], "b": f[3], "resultado": f[4]}
        for f in filas
    ])


if __name__ == "__main__":
    crear_tabla()
    app.run(host="0.0.0.0", port=5000)
