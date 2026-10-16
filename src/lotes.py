import sqlite3
import uuid

from flask import Blueprint, abort, g, render_template, request

from src.auditoria import registrar
from src.auth import login_requerido
<<<<<<< Updated upstream
from src.calculos import alertas_de, calcular_merma, costo_unitario, margen
=======
from src.calculos import MARGEN_OBJETIVO, UMBRAL_MERMA, alertas_de, calcular_merma, costo_unitario, margen, precio_sugerido
>>>>>>> Stashed changes
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
        with db:
            db.execute(
                "INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (codigo, productor, origen, fecha_rec, cantidad, usuario),
            )
            registrar(db, usuario, "crear", "lote", codigo, "cantidad", "", cantidad)
    except sqlite3.IntegrityError:
        raise ErrorValidacion(f"Ya existe un lote con el código {codigo}.") from None
    return codigo


def disponible(db, codigo):
    return db.execute(
        "SELECT recibido, consumido, disponible FROM v_inventario_lote WHERE codigo = ?",
        (codigo,),
    ).fetchone()


def filtrar_lotes(db, origen="", estado=""):
    return db.execute(
        "SELECT * FROM v_inventario_lote WHERE (? = '' OR origen = ?) AND (? = '' OR estados LIKE ?) "
        "ORDER BY codigo",
        (origen, origen, estado, f"%{estado}%"),
    ).fetchall()


def trazabilidad(db, codigo):
    lote = db.execute("SELECT * FROM v_inventario_lote WHERE codigo = ?", (codigo,)).fetchone()
    if lote is None:
        return None
    etapas = []
    for t in db.execute(
        "SELECT t.*, p.codigo AS producto, p.nombre, p.estado, p.motivo_estado, p.precio_venta "
        "FROM transformaciones t LEFT JOIN productos p ON p.transformacion_id = t.id "
        "WHERE t.lote_codigo = ? ORDER BY t.id",
        (codigo,),
    ):
        costo = costo_unitario(t["costo_total"], t["salida"])
        etapas.append({
            **dict(t),
            "merma": calcular_merma(t["entrada"], t["salida"]),
            "costo_unitario": costo,
            "margen": margen(t["precio_venta"], costo),
        })
    alertas = db.execute("SELECT * FROM alertas WHERE lote_codigo = ? ORDER BY id", (codigo,)).fetchall()
    return {"lote": lote, "etapas": etapas, "alertas": alertas}


@bp_lotes.route("/lotes")
@login_requerido
def lista_lotes():
    origen = request.args.get("origen", "")
    estado = request.args.get("estado", "")
    db = obtener_db()
    origenes = [r[0] for r in db.execute("SELECT DISTINCT origen FROM lotes ORDER BY origen")]
    return render_template("lotes.html", lotes=filtrar_lotes(db, origen, estado),
                           origenes=origenes, origen=origen, estado=estado)


@bp_lotes.route("/lotes/nuevo", methods=["GET", "POST"])
@login_requerido
def lote_nuevo():
    datos, mensaje, error = request.form, "", ""

    if request.method == "POST":
        try:
            codigo = crear_lote(obtener_db(), g.usuario, request.form)
            mensaje = f"Lote {codigo} guardado."
            datos = {}
        except ErrorValidacion as e:
            error = str(e)

    return render_template("lote_nuevo.html", datos=datos, mensaje=mensaje, error=error)


@bp_lotes.route("/lotes/<codigo>")
@login_requerido
def detalle(codigo):
    datos = trazabilidad(obtener_db(), codigo)
    if datos is None:
        abort(404)
    historial = []
    if g.rol == "admin":
        historial = obtener_db().execute(
            "SELECT * FROM auditoria WHERE entidad_id = ? OR entidad_id LIKE ? ORDER BY id DESC LIMIT 12",
            (codigo, f"P-{codigo}-%"),
        ).fetchall()
    return render_template("lote_detalle.html", error=request.args.get("error", ""),
                           historial=historial, **datos)


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
@login_requerido
def transformar(codigo):
    db = obtener_db()
    inventario = disponible(db, codigo)
    if inventario is None:
        abort(404)

    datos, mensaje, error = request.form, "", ""
    if request.method == "POST":
        try:
            resultado = registrar_transformacion(db, g.usuario, codigo, request.form)
            mensaje = ("Esta operación ya estaba registrada: no se consumió de nuevo."
                       if resultado == "repetida" else "Transformación registrada.")
            inventario = disponible(db, codigo)
            datos = {}
        except ErrorValidacion as e:
            error = str(e)

    op_id = datos.get("op_id") or str(uuid.uuid4())
    return render_template("transformar.html", codigo=codigo, inventario=inventario,
                           datos=datos, op_id=op_id, mensaje=mensaje, error=error,
                           umbral_merma=UMBRAL_MERMA, margen_objetivo=MARGEN_OBJETIVO)
