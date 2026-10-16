import sqlite3
from pathlib import Path

from flask import g

RUTA_DB = Path(__file__).resolve().parent.parent / "datos" / "cacao.db"
RUTA_SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def crear_tablas():
    RUTA_DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(RUTA_DB)
    esquema = RUTA_SCHEMA.read_text(encoding="utf-8")
    conn.executescript(esquema)
    _migrar_contacto_de_pedidos(conn, esquema)
    conn.close()


def _migrar_contacto_de_pedidos(conn, esquema):
    """Bases creadas con la primera versión de pedidos: 'contacto' pasa a teléfono y correo, y se agrega dirección."""
    if "contacto" not in {c[1] for c in conn.execute("PRAGMA table_info(pedidos)")}:
        return
    conn.row_factory = sqlite3.Row
    filas = [dict(f) for f in conn.execute("SELECT * FROM pedidos")]
    conn.executescript("""
        DROP VIEW IF EXISTS v_producto_disponible;
        DROP TRIGGER IF EXISTS trg_pedidos_solo_liberados;
        DROP TRIGGER IF EXISTS trg_pedidos_sin_sobreventa;
        DROP TRIGGER IF EXISTS trg_pedidos_estado_final;
        DROP TRIGGER IF EXISTS trg_pedidos_no_borrar;
        DROP TABLE pedidos;
    """)
    conn.executescript(esquema)
    # Los pedidos históricos se copian tal cual, sin las reglas que solo aplican a pedidos nuevos
    conn.executescript("DROP TRIGGER trg_pedidos_solo_liberados; DROP TRIGGER trg_pedidos_sin_sobreventa;")
    with conn:
        for f in filas:
            es_correo = "@" in f["contacto"]
            conn.execute(
                "INSERT INTO pedidos (id, token, producto_codigo, comprador, direccion, telefono, correo, kilos, "
                "precio_kg, estado, motivo_estado, creado_en, actualizado_en) "
                "VALUES (?, ?, ?, ?, 'Sin registrar', ?, ?, ?, ?, ?, ?, ?, ?)",
                (f["id"], f["token"], f["producto_codigo"], f["comprador"],
                 "Sin registrar" if es_correo else f["contacto"],
                 f["contacto"] if es_correo else "sin-registrar@kaoka.local",
                 f["kilos"], f["precio_kg"], f["estado"], f["motivo_estado"], f["creado_en"], f["actualizado_en"]))
    conn.executescript(esquema)


def obtener_db():
    if "db" not in g:
        g.db = sqlite3.connect(RUTA_DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def cerrar_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
