import os

import click
from flask import Flask, redirect, render_template, url_for
from werkzeug.security import generate_password_hash

from src import respaldo
from src.auth import bp_auth
from src.db import cerrar_db, crear_tablas, obtener_db
from src.lotes import bp_lotes, crear_lote
from src.productos import bp_productos
from src.validaciones import ErrorValidacion

USUARIOS_DEMO = [("operador", "operador123", "operador"), ("admin", "admin123", "admin")]
LOTES_DEMO = [
    {"codigo": "CAC001", "productor": "Productor A", "origen": "Rivera", "fecha_recepcion": "2026-10-15", "cantidad": "100"},
    {"codigo": "CAC002", "productor": "Productor B", "origen": "Campoalegre", "fecha_recepcion": "2026-10-15", "cantidad": "150"},
    {"codigo": "CAC003", "productor": "Productor C", "origen": "Algeciras", "fecha_recepcion": "2026-10-15", "cantidad": "80"},
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("CACAO_SECRET", "solo-para-desarrollo")
app.teardown_appcontext(cerrar_db)
app.register_blueprint(bp_auth)
app.register_blueprint(bp_lotes)
app.register_blueprint(bp_productos)
respaldo.registrar_comandos(app)
crear_tablas()


@app.route("/")
def inicio():
    return redirect(url_for("lotes.lista_lotes"))


@app.errorhandler(403)
def prohibido(_error):
    return render_template("error.html", mensaje="Acción denegada: su rol no tiene permiso."), 403


@app.errorhandler(404)
def no_encontrado(_error):
    return render_template("error.html", mensaje="La página o el registro no existe."), 404


@app.cli.command("cargar-demo")
def cargar_demo():
    db = obtener_db()
    with db:
        for usuario, clave, rol in USUARIOS_DEMO:
            db.execute("INSERT OR IGNORE INTO usuarios (usuario, clave_hash, rol) VALUES (?, ?, ?)",
                       (usuario, generate_password_hash(clave), rol))
    for lote in LOTES_DEMO:
        try:
            crear_lote(db, "sistema", lote)
        except ErrorValidacion:
            pass
    click.echo("Listo. Usuarios: operador/operador123 y admin/admin123")
