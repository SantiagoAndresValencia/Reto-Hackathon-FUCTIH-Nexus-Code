import sqlite3
from pathlib import Path

from flask import g

RUTA_DB = Path(__file__).resolve().parent.parent / "datos" / "cacao.db"
RUTA_SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def crear_tablas():
    
    RUTA_DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(RUTA_DB)
    conn.executescript(RUTA_SCHEMA.read_text(encoding="utf-8"))
    conn.close()


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