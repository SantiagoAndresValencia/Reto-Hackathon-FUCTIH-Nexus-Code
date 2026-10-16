from functools import wraps

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from src.auditoria import registrar
from src.db import obtener_db

bp_auth = Blueprint("auth", __name__)


class PermisoDenegado(Exception):
    pass


def exigir_admin(db, usuario, rol, accion, entidad, entidad_id):
    if rol != "admin":
        with db:
            registrar(db, usuario, f"DENEGADO: {accion}", entidad, entidad_id, "rol", "", rol)
        raise PermisoDenegado(accion)


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("auth.login"))
        g.usuario, g.rol = session["usuario"], session["rol"]
        return vista(*args, **kwargs)
    return envoltura


def solo_admin(vista):
    @wraps(vista)
    @login_requerido
    def envoltura(*args, **kwargs):
        if g.rol != "admin":
            db = obtener_db()
            with db:
                registrar(db, g.usuario, f"DENEGADO: {request.path}", "ruta", request.path, "rol", "", g.rol)
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        fila = obtener_db().execute(
            "SELECT usuario, clave_hash, rol FROM usuarios WHERE usuario = ?",
            (request.form.get("usuario", "").strip(),),
        ).fetchone()
        if fila and check_password_hash(fila["clave_hash"], request.form.get("clave", "")):
            session.clear()
            session["usuario"], session["rol"] = fila["usuario"], fila["rol"]
            return redirect(url_for("lotes.lista_lotes"))
        error = "Usuario o contraseña incorrectos."
    return render_template("login.html", error=error)


@bp_auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp_auth.route("/admin/auditoria")
@solo_admin
def auditoria():
    filtro = request.args.get("q", "").strip().upper()
    filas = obtener_db().execute(
        "SELECT * FROM auditoria WHERE entidad_id LIKE ? ORDER BY id DESC", (f"%{filtro}%",)
    ).fetchall()
    return render_template("auditoria.html", filas=filas, q=filtro)