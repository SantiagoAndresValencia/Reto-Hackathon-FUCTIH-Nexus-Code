import sqlite3
import uuid

from flask import Blueprint, abort, render_template, request, session

from src.auditoria import registrar
from src.calculos import alertas_de
from src.db import obtener_db
from src.validaciones import ErrorValidacion, fecha, numero_no_negativo, numero_positivo, texto

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


def registrar_transformacion(db, usuario, lote, formulario):
    op_id = texto(formulario.get("op_id"), "Operación")
    etapa = texto(formulario.get("etapa"), "Etapa")
    responsable = texto(formulario.get("responsable"), "Responsable")
    fecha_t = fecha(formulario.get("fecha"), "Fecha")
    entrada = numero_positivo(formulario.get("entrada"), "Entrada")
    salida = numero_no_negativo(formulario.get("salida"), "Salida")
    costo_total = numero_no_negativo(formulario.get("costo_total"), "Costo total")
    precio = numero_positivo(formulario.get("precio_venta"), "Precio de venta")
    producto = texto(formulario.get("producto"), "Producto")
    costos_incluidos = formulario.get("costos_incluidos", "").strip()
    justificacion = formulario.get("justificacion", "").strip()
    incidencias = formulario.get("incidencias", "").strip()

    if salida > entrada and not justificacion:
        raise ErrorValidacion("La salida supera la entrada: escriba la justificación.")
    if costo_total > 0 and not costos_incluidos:
        raise ErrorValidacion("Indique qué costos incluye el costo total.")

    try:
        with db:
            cur = db.execute(
                "INSERT INTO transformaciones (op_id, lote_codigo, etapa, responsable, fecha, entrada, "
                "salida, costo_total, costos_incluidos, incidencias, justificacion, creado_por) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (op_id, lote, etapa, responsable, fecha_t, entrada, salida, costo_total,
                 costos_incluidos, incidencias, justificacion, usuario),
            )
            transformacion_id = cur.lastrowid

            if salida > 0:
                numero = db.execute(
                    "SELECT COUNT(*) FROM productos WHERE lote_codigo = ?", (lote,)
                ).fetchone()[0] + 1
                db.execute(
                    "INSERT INTO productos (codigo, transformacion_id, lote_codigo, nombre, cantidad, precio_venta) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f"P-{lote}-{numero}", transformacion_id, lote, producto, salida, precio),
                )

            for tipo, regla, causa in alertas_de(entrada, salida, costo_total, precio):
                db.execute(
                    "INSERT INTO alertas (lote_codigo, transformacion_id, tipo, regla, causa) VALUES (?, ?, ?, ?, ?)",
                    (lote, transformacion_id, tipo, regla, causa),
                )

            registrar(db, usuario, "transformar", "lote", lote, "consumido", "", entrada)
    except sqlite3.IntegrityError as e:
        if "op_id" in str(e):
            return "repetida"
        if "INVENTARIO_INSUFICIENTE" in str(e):
            raise ErrorValidacion(f"No hay suficiente cacao disponible en {lote}.") from None
        raise
    return "registrada"


@bp_lotes.route("/lotes/<codigo>/transformar", methods=["GET", "POST"])
def transformar(codigo):
    db = obtener_db()
    inventario = disponible(db, codigo)
    if inventario is None:
        abort(404)

    datos, mensaje, error = request.form, "", ""
    if request.method == "POST":
        try:
            resultado = registrar_transformacion(db, session.get("usuario", "sin-sesion"), codigo, request.form)
            mensaje = ("Esta operación ya estaba registrada: no se consumió de nuevo."
                       if resultado == "repetida" else "Transformación registrada.")
            inventario = disponible(db, codigo)
            datos = {}
        except ErrorValidacion as e:
            error = str(e)

    op_id = datos.get("op_id") or str(uuid.uuid4())
    return render_template("transformar.html", codigo=codigo, inventario=inventario,
                           datos=datos, op_id=op_id, mensaje=mensaje, error=error)
