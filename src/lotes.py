import sqlite3

from flask import Blueprint, render_template, request, session

from src.db import obtener_db
from src.validaciones import ErrorValidacion, fecha, numero_positivo, texto

bp_lotes = Blueprint("lotes", __name__)


def crear_lote(db, usuario, formulario):
    codigo = texto(formulario.get("codigo"), "Código").upper()
    productor = texto(formulario.get("productor"), "Productor")
    origen = texto(formulario.get("origen"), "Origen")
    fecha_rec = fecha(formulario.get("fecha_recepcion"), "Fecha")
    cantidad = numero_positivo(formulario.get("cantidad"), "Cantidad")

    try:
        db.execute(
            "INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (codigo, productor, origen, fecha_rec, cantidad, usuario),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise ErrorValidacion(f"Ya existe un lote con el código {codigo}.")
    return codigo


def disponible(db, codigo):
    return db.execute(
        "SELECT recibido, consumido, disponible FROM v_inventario_lote WHERE codigo = ?",
        (codigo,),
    ).fetchone()


@bp_lotes.route("/lotes")
def lista_lotes():
    lotes = obtener_db().execute(
        "SELECT codigo, origen, recibido, disponible, unidad FROM v_inventario_lote ORDER BY codigo"
    ).fetchall()
    return render_template("lotes.html", lotes=lotes)


@bp_lotes.route("/lotes/nuevo", methods=["GET", "POST"])
def lote_nuevo():
    datos, mensaje, error = request.form, "", ""

    if request.method == "POST":
        try:
            codigo = crear_lote(obtener_db(), session.get("usuario", "sin-sesion"), request.form)
            mensaje = f"Lote {codigo} guardado."
            datos = {}
        except ErrorValidacion as e:
            error = str(e)

    return render_template("lote_nuevo.html", datos=datos, mensaje=mensaje, error=error)
