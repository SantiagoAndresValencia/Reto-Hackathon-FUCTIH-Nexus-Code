from datetime import datetime

from flask import Blueprint, render_template, request, session

from src.db import obtener_db
from src.validaciones import ErrorValidacion, fecha, numero_positivo, texto

bp_lotes = Blueprint("lotes", __name__)


@bp_lotes.route("/lotes/nuevo", methods=["GET", "POST"])
def lote_nuevo():
    mensaje = ""
    error = ""

    if request.method == "POST":
        try:
            # Revisar los datos, si hay error se lanza ErrorValidacion
            codigo = texto(request.form.get("codigo"), "Código").upper()
            productor = texto(request.form.get("productor"), "Productor")
            origen = texto(request.form.get("origen"), "Origen")
            fecha_rec = fecha(request.form.get("fecha_recepcion"), "Fecha")
            cantidad = numero_positivo(request.form.get("cantidad"), "Cantidad")

            # Validacion codigo existente
            db = obtener_db()
            existe = db.execute("SELECT codigo FROM lotes WHERE codigo = ?", (codigo,)).fetchone()

            if existe:
                error = f"Ya existe un lote con el código {codigo}."
            else:
                # Guardar el lote
                usuario = session.get("usuario", "sin-sesion")
                ahora = datetime.now().isoformat(timespec="seconds")
                db.execute(
                    "INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, unidad, creado_por, creado_en) "
                    "VALUES (?, ?, ?, ?, ?, 'kg', ?, ?)",
                    (codigo, productor, origen, fecha_rec, cantidad, usuario, ahora),
                )
                db.commit()
                mensaje = f"Lote {codigo} guardado."

        except ErrorValidacion as e:
            error = str(e)

    return render_template("lote_nuevo.html", mensaje=mensaje, error=error, datos=request.form)