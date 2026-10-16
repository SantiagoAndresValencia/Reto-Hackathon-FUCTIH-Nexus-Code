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
    if "municipio" not in {c[1] for c in conn.execute("PRAGMA table_info(pedidos)")}:
        conn.execute("ALTER TABLE pedidos ADD COLUMN municipio TEXT NOT NULL DEFAULT 'Sin registrar'")
        conn.commit()
    _migrar_estados_de_pedidos(conn, esquema)
    conn.close()


def _migrar_estados_de_pedidos(conn, esquema):
    """Bases anteriores a los estados enviado y entregado: se rehace la tabla con la regla nueva y se copian los pedidos."""
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'pedidos'").fetchone()[0]
    if "'enviado'" in sql:
        return
    columnas = [c[1] for c in conn.execute("PRAGMA table_info(pedidos)")]
    filas = conn.execute(f"SELECT {', '.join(columnas)} FROM pedidos").fetchall()
    conn.executescript("""
        DROP VIEW IF EXISTS v_producto_disponible;
        DROP TRIGGER IF EXISTS trg_pedidos_solo_liberados;
        DROP TRIGGER IF EXISTS trg_pedidos_sin_sobreventa;
        DROP TRIGGER IF EXISTS trg_pedidos_estado_final;
        DROP TRIGGER IF EXISTS trg_pedidos_transicion;
        DROP TRIGGER IF EXISTS trg_pedidos_no_borrar;
        DROP TABLE pedidos;
    """)
    conn.executescript(esquema)
    conn.executescript("DROP TRIGGER trg_pedidos_solo_liberados; DROP TRIGGER trg_pedidos_sin_sobreventa;")
    with conn:
        conn.executemany(f"INSERT INTO pedidos ({', '.join(columnas)}) VALUES ({', '.join('?' * len(columnas))})", filas)
    conn.executescript(esquema)


def _migrar_contacto_de_pedidos(conn, esquema):
    """Bases creadas con la primera versión de pedidos: 'contacto' pasa a teléfono y correo, y se agregan municipio y dirección."""
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
                "INSERT INTO pedidos (id, token, producto_codigo, comprador, municipio, direccion, telefono, correo, "
                "kilos, precio_kg, estado, motivo_estado, creado_en, actualizado_en) "
                "VALUES (?, ?, ?, ?, 'Sin registrar', 'Sin registrar', ?, ?, ?, ?, ?, ?, ?, ?)",
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
