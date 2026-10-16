import csv
import io

import segno

from flask import Blueprint, Response, abort, g, redirect, render_template, request, url_for

from src.auditoria import registrar
from src.auth import PermisoDenegado, exigir_admin, login_requerido, solo_admin
from src.db import obtener_db
from src.lotes import filtrar_lotes
from src.validaciones import ErrorValidacion, texto

bp_productos = Blueprint("productos", __name__)

ESTADOS = ("liberado", "bloqueado")


def cambiar_estado(db, usuario, rol, codigo, estado, motivo):
    exigir_admin(db, usuario, rol, f"cambiar estado a {estado}", "producto", codigo)
    if estado not in ESTADOS:
        raise ErrorValidacion("Estado no válido.")
    motivo = texto(motivo, "Motivo")
    producto = db.execute("SELECT estado FROM productos WHERE codigo = ?", (codigo,)).fetchone()
    if producto is None:
        raise ErrorValidacion(f"El producto {codigo} no existe.")
    with db:
        db.execute("UPDATE productos SET estado = ?, motivo_estado = ? WHERE codigo = ?",
                   (estado, motivo, codigo))
        registrar(db, usuario, f"cambiar estado ({motivo})", "producto", codigo,
                  "estado", producto["estado"], estado)


def bloquear_lote(db, usuario, rol, lote, motivo):
    """Hora 12: bloquea en una transacción todos los productos del lote que no estén bloqueados."""
    exigir_admin(db, usuario, rol, "bloquear lote completo", "lote", lote)
    motivo = texto(motivo, "Motivo")
    productos = db.execute("SELECT codigo, estado, cantidad FROM productos WHERE lote_codigo = ? AND estado != 'bloqueado'",
                           (lote,)).fetchall()
    if not productos:
        raise ErrorValidacion(f"El lote {lote} no tiene productos por bloquear.")
    with db:
        for p in productos:
            db.execute("UPDATE productos SET estado = 'bloqueado', motivo_estado = ? WHERE codigo = ?", (motivo, p["codigo"]))
            registrar(db, usuario, f"bloquear lote ({motivo})", "producto", p["codigo"], "estado", p["estado"], "bloqueado")
        registrar(db, usuario, f"bloquear lote ({motivo})", "lote", lote, "productos bloqueados", "", len(productos))
    return len(productos), sum(p["cantidad"] for p in productos)


def ficha_publica(db, codigo):
    return db.execute(
        "SELECT codigo_producto, nombre, cantidad, unidad, precio_venta, estado, en_venta, lote_codigo, "
        "origen, fecha_recepcion, etapa, fecha_transformacion "
        "FROM v_ficha_publica WHERE codigo_producto = ?",
        (codigo.upper(),),
    ).fetchone()


def disponible_producto(db, codigo):
    fila = db.execute("SELECT disponible FROM v_producto_disponible WHERE codigo = ?", (codigo,)).fetchone()
    return fila["disponible"] if fila else 0


def resumen_csv(db, origen="", estado=""):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["codigo", "origen", "recibido_kg", "consumido_kg", "disponible_kg",
                       "estados", "costo_total_cop"])
    for l in filtrar_lotes(db, origen, estado):
        escritor.writerow([_celda_segura(l["codigo"]), _celda_segura(l["origen"]), l["recibido"],
                           l["consumido"], l["disponible"], l["estados"], l["costo_total"]])
    return salida.getvalue()


def _celda_segura(valor):
    if str(valor).startswith(("=", "+", "-", "@")):
        return "'" + str(valor)
    return valor


@bp_productos.route("/productos/<codigo>/estado", methods=["POST"])
@login_requerido
def estado(codigo):
    db = obtener_db()
    fila = db.execute("SELECT lote_codigo FROM productos WHERE codigo = ?", (codigo,)).fetchone()
    if fila is None:
        abort(404)
    lote = fila["lote_codigo"]
    try:
        cambiar_estado(db, g.usuario, g.rol, codigo, request.form.get("estado"), request.form.get("motivo"))
    except PermisoDenegado:
        abort(403)
    except ErrorValidacion as e:
        return redirect(url_for("lotes.detalle", codigo=lote, error=str(e)))
    return redirect(url_for("lotes.detalle", codigo=lote))


@bp_productos.route("/lotes/<codigo>/bloquear", methods=["POST"])
@login_requerido
def bloquear(codigo):
    codigo = codigo.upper()
    db = obtener_db()
    if db.execute("SELECT 1 FROM lotes WHERE codigo = ?", (codigo,)).fetchone() is None:
        abort(404)
    try:
        cantidad, kg = bloquear_lote(db, g.usuario, g.rol, codigo, request.form.get("motivo"))
    except PermisoDenegado:
        abort(403)
    except ErrorValidacion as e:
        return redirect(url_for("lotes.detalle", codigo=codigo, error=str(e)))
    return redirect(url_for("lotes.detalle", codigo=codigo,
                            mensaje=f"Lote {codigo} bloqueado: {cantidad} producto(s), {kg:g} kg afectados."))


@bp_productos.route("/productos/<codigo>/etiqueta")
@login_requerido
def etiqueta(codigo):
    datos = ficha_publica(obtener_db(), codigo)
    if datos is None:
        abort(404)
    enlace = url_for("productos.ficha", codigo=datos["codigo_producto"], _external=True)
    qr = segno.make(enlace, error="m").svg_inline(scale=6, border=2, dark="#2b1a10", omitsize=True)
    local = request.host.split(":")[0] in ("127.0.0.1", "localhost")
    return render_template("etiqueta.html", f=datos, enlace=enlace, qr=qr, local=local)


def catalogo(db, origen="", etapa=""):
    """Productos liberados para la venta, solo con datos públicos."""
    consulta = ("SELECT f.codigo_producto, f.nombre, f.cantidad, f.unidad, f.precio_venta, f.lote_codigo, "
                "f.origen, f.etapa, f.fecha_transformacion, d.disponible FROM v_ficha_publica f "
                "JOIN v_producto_disponible d ON d.codigo = f.codigo_producto WHERE f.en_venta = 1")
    parametros = []
    if origen:
        consulta += " AND f.origen = ?"
        parametros.append(origen)
    if etapa:
        consulta += " AND f.etapa = ?"
        parametros.append(etapa)
    return db.execute(consulta + " ORDER BY d.disponible <= 0, f.fecha_transformacion DESC, f.codigo_producto", parametros).fetchall()


@bp_productos.route("/comprador")
def comprador():
    db = obtener_db()
    codigo = request.args.get("codigo", "").strip().upper()
    error = None
    if codigo:
        if ficha_publica(db, codigo):
            return redirect(url_for("productos.ficha", codigo=codigo))
        error = f"No encontramos el producto {codigo}. Revise el código impreso en el empaque."
    origen = request.args.get("origen", "")
    etapa = request.args.get("etapa", "")
    disponibles = db.execute("SELECT DISTINCT origen, etapa FROM v_ficha_publica WHERE en_venta = 1").fetchall()
    return render_template("comprador.html", productos=catalogo(db, origen, etapa),
                           origenes=sorted({d["origen"] for d in disponibles}),
                           etapas=sorted({d["etapa"] for d in disponibles}),
                           origen=origen, etapa=etapa, codigo=codigo, error=error,
                           pedido=request.args.get("pedido", ""), error_pedido=request.args.get("error_pedido"))


@bp_productos.route("/consultar")
def consultar():
    return redirect(url_for("productos.comprador", **request.args))


@bp_productos.route("/ficha/<codigo>")
def ficha(codigo):
    db = obtener_db()
    datos = ficha_publica(db, codigo)
    if datos is None:
        abort(404)
    return render_template("ficha.html", f=datos, disponible=disponible_producto(db, datos["codigo_producto"]), form={})


@bp_productos.route("/admin/exportar.csv")
@solo_admin
def exportar():
    contenido = resumen_csv(obtener_db(), request.args.get("origen", ""), request.args.get("estado", ""))
    return Response(contenido, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=resumen_lotes.csv"})
