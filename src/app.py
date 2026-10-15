from flask import Flask

from src.db import cerrar_db, crear_tablas
from src.lotes import bp_lotes

app = Flask(__name__)
app.teardown_appcontext(cerrar_db)
crear_tablas()
app.register_blueprint(bp_lotes)


@app.route("/")
def inicio():
    return "Hola, Mundo"