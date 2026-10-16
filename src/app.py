from flask import Flask, redirect, url_for

from src.db import cerrar_db, crear_tablas
from src.lotes import bp_lotes

app = Flask(__name__)
app.teardown_appcontext(cerrar_db)
app.register_blueprint(bp_lotes)
crear_tablas()


@app.route("/")
def inicio():
    return redirect(url_for("lotes.lista_lotes"))
