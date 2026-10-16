import re
import secrets
import sqlite3

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from src.auditoria import registrar
from src.auth import PermisoDenegado, exigir_admin, login_requerido, solo_admin
from src.db import obtener_db
from src.productos import disponible_producto, ficha_publica
from src.validaciones import ErrorValidacion, correo, numero_positivo, telefono, texto

bp_pedidos = Blueprint("pedidos", __name__)

ESTADOS_ADMIN = ("aprobado", "rechazado")
ACTIVOS = ("pendiente", "aprobado")
COLUMNAS = ("SELECT d.*, printf('PED-%04d', d.id) AS numero, d.kilos * d.precio_kg AS total, "
            "p.nombre, p.unidad, p.estado AS estado_producto, p.lote_codigo "
            "FROM pedidos d JOIN productos p ON p.codigo = d.producto_codigo ")


def numero_a_id(numero):
    """'PED-0007' o '7' -> 7; None si no tiene esa forma."""
    numero = (numero or "").strip().upper().removeprefix("PED-").removeprefix("PED")
    return int(numero) if numero.isdigit() else None


def crear_pedido(db, codigo_producto, datos):
    producto = ficha_publica(db, codigo_producto)
    if producto is None:
        raise ErrorValidacion(f"El producto {codigo_producto} no existe.")
    if not producto["en_venta"]:
        raise ErrorValidacion("Este producto no está disponible para la venta.")
    kilos = numero_positivo(datos.get("kilos"), "Kilos")
    comprador = texto(datos.get("comprador"), "Nombre o empresa")
    direccion = texto(datos.get("direccion"), "Dirección de entrega")
    tel = telefono(datos.get("telefono"), "Teléfono")
    email = correo(datos.get("correo"), "Correo")
    libre = disponible_producto(db, producto["codigo_producto"])
    if kilos > libre + 0.000001:
        cifra = f"{max(libre, 0):g}".replace(".", ",")
        raise ErrorValidacion(f"Solo quedan {cifra} {producto['unidad']} disponibles.")
    token = secrets.token_urlsafe(18)
    try:
        with db:
            cursor = db.execute(
                "INSERT INTO pedidos (token, producto_codigo, comprador, direccion, telefono, correo, kilos, precio_kg) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (token, producto["codigo_producto"], comprador, direccion, tel, email, kilos, producto["precio_venta"]))
            numero = f"PED-{cursor.lastrowid:04d}"
            registrar(db, "comprador", "crear pedido", "pedido", numero, "kilos", "", f"{kilos:g}")
    except sqlite3.IntegrityError as e:
        raise ErrorValidacion("No hay inventario suficiente para ese pedido." if "INVENTARIO" in str(e)
                              else "Este producto no está disponible para la venta.") from None
    return token


def pedido_por_token(db, token):
    return db.execute(COLUMNAS + "WHERE d.token = ?", (token,)).fetchone()


def cancelar_pedido(db, token, motivo):
    pedido = pedido_por_token(db, token)
    if pedido is None:
        raise ErrorValidacion("El pedido no existe.")
    if pedido["estado"] not in ACTIVOS:
        raise ErrorValidacion(f"El pedido ya está {pedido['estado']} y no se puede cancelar.")
    motivo = texto(motivo, "Razón de la cancelación")
    with db:
        db.execute("UPDATE pedidos SET estado = 'cancelado', motivo_estado = ?, "
                   "actualizado_en = datetime('now', 'localtime') WHERE id = ?", (motivo, pedido["id"]))
        registrar(db, "comprador", f"cancelar pedido ({motivo})", "pedido", pedido["numero"],
                  "estado", pedido["estado"], "cancelado")


def cambiar_estado_pedido(db, usuario, rol, numero, estado, motivo):
    exigir_admin(db, usuario, rol, f"pedido {estado}", "pedido", numero)
    if estado not in ESTADOS_ADMIN:
        raise ErrorValidacion("Estado no válido.")
    motivo = texto(motivo, "Motivo")
    pedido = db.execute(COLUMNAS + "WHERE d.id = ?", (numero_a_id(numero),)).fetchone()
    if pedido is None:
        raise ErrorValidacion(f"El pedido {numero} no existe.")
    if pedido["estado"] not in ACTIVOS:
        raise ErrorValidacion(f"El pedido {numero} ya está {pedido['estado']}: no se puede cambiar.")
    if estado == "aprobado" and pedido["estado_producto"] != "liberado":
        raise ErrorValidacion(f"El producto {pedido['producto_codigo']} está {pedido['estado_producto']}: "
                              "libérelo antes de aprobar el pedido.")
    with db:
        db.execute("UPDATE pedidos SET estado = ?, motivo_estado = ?, "
                   "actualizado_en = datetime('now', 'localtime') WHERE id = ?", (estado, motivo, pedido["id"]))
        registrar(db, usuario, f"pedido {estado} ({motivo})", "pedido", pedido["numero"],
                  "estado", pedido["estado"], estado)


@bp_pedidos.route("/ficha/<codigo>/pedido", methods=["POST"])
def nuevo(codigo):
    db = obtener_db()
    try:
        token = crear_pedido(db, codigo.upper(), request.form)
    except ErrorValidacion as e:
        datos = ficha_publica(db, codigo)
        if datos is None:
            abort(404)
        return render_template("ficha.html", f=datos, disponible=disponible_producto(db, datos["codigo_producto"]),
                               error_pedido=str(e), form=request.form), 400
    return redirect(url_for("pedidos.seguimiento", token=token, nuevo=1))


@bp_pedidos.route("/pedido/<token>")
def seguimiento(token):
    pedido = pedido_por_token(obtener_db(), token)
    if pedido is None:
        abort(404)
    return render_template("pedido.html", p=pedido, nuevo=request.args.get("nuevo"),
                           error=request.args.get("error"))


@bp_pedidos.route("/pedido/<token>/cancelar", methods=["POST"])
def cancelar(token):
    try:
        cancelar_pedido(obtener_db(), token, request.form.get("motivo"))
    except ErrorValidacion as e:
        return redirect(url_for("pedidos.seguimiento", token=token, error=str(e)))
    return redirect(url_for("pedidos.seguimiento", token=token))


@bp_pedidos.route("/pedidos/buscar")
def buscar():
    """El comprador recupera su pedido con el número y el teléfono o el correo que dejó."""
    numero = request.args.get("numero", "").strip().upper()
    contacto = request.args.get("contacto", "").strip().lower()
    fila = obtener_db().execute("SELECT token, telefono, correo FROM pedidos WHERE id = ?",
                                (numero_a_id(numero),)).fetchone()
    solo_digitos = re.sub(r"\D", "", contacto)
    if fila and contacto and (contacto == fila["correo"].lower()
                              or (solo_digitos and solo_digitos == re.sub(r"\D", "", fila["telefono"]))):
        return redirect(url_for("pedidos.seguimiento", token=fila["token"]))
    return redirect(url_for("productos.comprador", pedido=numero, error_pedido=1) + "#seguir-pedido")


@bp_pedidos.route("/admin/pedidos")
@solo_admin
def lista():
    db = obtener_db()
    estado = request.args.get("estado", "")
    consulta, parametros = COLUMNAS, []
    if estado:
        consulta += "WHERE d.estado = ? "
        parametros.append(estado)
    pedidos = db.execute(consulta + "ORDER BY d.estado != 'pendiente', d.id DESC", parametros).fetchall()
    conteo = dict(db.execute("SELECT estado, COUNT(*) FROM pedidos GROUP BY estado").fetchall())
    apartado = db.execute("SELECT COALESCE(SUM(kilos), 0) FROM pedidos WHERE estado IN ('pendiente', 'aprobado')").fetchone()[0]
    return render_template("pedidos.html", pedidos=pedidos, conteo=conteo, apartado=apartado,
                           estado=estado, error=request.args.get("error"))


@bp_pedidos.route("/admin/pedidos/<numero>/estado", methods=["POST"])
@login_requerido
def estado(numero):
    try:
        cambiar_estado_pedido(obtener_db(), g.usuario, g.rol, numero,
                              request.form.get("estado"), request.form.get("motivo"))
    except PermisoDenegado:
        abort(403)
    except ErrorValidacion as e:
        return redirect(url_for("pedidos.lista", error=str(e)))
    return redirect(url_for("pedidos.lista"))
