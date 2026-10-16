import csv
import io

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


def ficha_publica(db, codigo):
    return db.execute(
        "SELECT codigo_producto, nombre, cantidad, unidad, estado, en_venta, lote_codigo, "
        "origen, fecha_recepcion, etapa, fecha_transformacion "
        "FROM v_ficha_publica WHERE codigo_producto = ?",
        (codigo.upper(),),
    ).fetchone()


def resumen_csv(db, origen="", estado=""):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["codigo", "origen", "recibido_kg", "consumido_kg", "disponible_kg",
                       "estados", "costo_total_cop"])
    for l in filtrar_lotes(db, origen, estado):
        escritor.writerow([l["codigo"], l["origen"], l["recibido"], l["consumido"],
                           l["disponible"], l["estados"], l["costo_total"]])
    return salida.getvalue()


@bp_productos.route("/productos/<codigo>/estado", methods=["POST"])
@login_requerido
def estado(codigo):
    db = obtener_db()
    lote = request.form.get("lote", "")
    try:
        cambiar_estado(db, g.usuario, g.rol, codigo, request.form.get("estado"), request.form.get("motivo"))
    except PermisoDenegado:
        abort(403)
    except ErrorValidacion as e:
        return redirect(url_for("lotes.detalle", codigo=lote, error=str(e)))
    return redirect(url_for("lotes.detalle", codigo=lote))


@bp_productos.route("/ficha/<codigo>")
def ficha(codigo):
    datos = ficha_publica(obtener_db(), codigo)
    if datos is None:
        abort(404)
    return render_template("ficha.html", f=datos)


@bp_productos.route("/admin/exportar.csv")
@solo_admin
def exportar():
    contenido = resumen_csv(obtener_db(), request.args.get("origen", ""), request.args.get("estado", ""))
    return Response(contenido, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=resumen_lotes.csv"})
