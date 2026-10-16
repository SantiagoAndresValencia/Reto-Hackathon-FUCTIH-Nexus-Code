import os
import secrets

import click
from flask import Flask, redirect, render_template, url_for
from werkzeug.security import generate_password_hash

from src import casos, respaldo
from src.auth import bp_auth
from src.db import cerrar_db, crear_tablas, obtener_db
from src.lotes import bp_lotes, crear_lote
from src.pedidos import bp_pedidos
from src.productos import bp_productos
from src.validaciones import MUNICIPIOS_HUILA, ErrorValidacion

USUARIOS_DEMO = [("operador", "operador123", "operador"), ("admin", "admin123", "admin")]
LOTES_DEMO = [
    {"codigo": "CAC001", "productor": "Productor A", "origen": "Rivera", "fecha_recepcion": "2026-10-15", "cantidad": "100"},
    {"codigo": "CAC002", "productor": "Productor B", "origen": "Campoalegre", "fecha_recepcion": "2026-10-15", "cantidad": "150"},
    {"codigo": "CAC003", "productor": "Productor C", "origen": "Algeciras", "fecha_recepcion": "2026-10-15", "cantidad": "80"},
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("CACAO_SECRET") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.teardown_appcontext(cerrar_db)


@app.url_defaults
def version_de_estaticos(endpoint, valores):
    """kaoka.css?v=<fecha de modificación>: al cambiar el archivo (o de rama) el navegador pide la copia nueva."""
    if endpoint == "static" and "filename" in valores:
        ruta = os.path.join(app.static_folder, valores["filename"])
        if os.path.isfile(ruta):
            valores["v"] = int(os.stat(ruta).st_mtime)
app.jinja_env.globals["MUNICIPIOS_HUILA"] = MUNICIPIOS_HUILA
app.register_blueprint(bp_auth)
app.register_blueprint(bp_lotes)
app.register_blueprint(bp_productos)
app.register_blueprint(bp_pedidos)
respaldo.registrar_comandos(app)
casos.registrar_comando(app)
crear_tablas()


@app.template_filter("kg")
def formato_kg(valor):
    """100.0 -> '100', 12.5 -> '12,5'."""
    return f"{valor:g}".replace(".", ",") if valor is not None else "—"


@app.template_filter("miles")
@app.template_filter("cop")
def formato_miles(valor):
    """1600000 -> '1.600.000'."""
    return f"{valor:,.0f}".replace(",", ".") if valor is not None else "—"


@app.route("/")
def inicio():
    return redirect(url_for("lotes.lista_lotes"))


@app.errorhandler(403)
def prohibido(_error):
    return render_template("error.html", mensaje_error="Acción denegada: su rol no tiene permiso."), 403


@app.errorhandler(404)
def no_encontrado(_error):
    return render_template("error.html", mensaje_error="La página o el registro no existe."), 404


@app.errorhandler(500)
def error_interno(_error):
    return render_template("error.html", mensaje_error="Ocurrió un error inesperado. No se guardó nada a medias."), 500


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
