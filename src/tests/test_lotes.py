import sqlite3
from pathlib import Path

import pytest

from src.lotes import crear_lote, disponible
from src.validaciones import ErrorValidacion, fecha, numero_positivo, texto

SCHEMA = Path(__file__).resolve().parent.parent / "schema.sql"
LOTE = {"codigo": "cac004", "productor": "Productor D", "origen": "Neiva",
        "fecha_recepcion": "2026-10-15", "cantidad": "50"}


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    yield conn
    conn.close()


@pytest.mark.parametrize("valor", ["", "   ", None])
def test_texto_obligatorio(valor):
    with pytest.raises(ErrorValidacion):
        texto(valor, "Productor")


@pytest.mark.parametrize("valor", ["0", "-5", "abc", "nan"])
def test_cantidad_debe_ser_positiva(valor):
    with pytest.raises(ErrorValidacion):
        numero_positivo(valor, "Cantidad")


def test_acepta_coma_decimal():
    assert numero_positivo("12,5", "Cantidad") == 12.5


def test_fecha_inexistente():
    with pytest.raises(ErrorValidacion):
        fecha("2026-13-40", "Fecha")


def test_crea_lote_y_queda_disponible(db):
    assert crear_lote(db, "operador", LOTE) == "CAC004"
    inv = disponible(db, "CAC004")
    assert (inv["recibido"], inv["consumido"], inv["disponible"]) == (50, 0, 50)


def test_lote_invalido_no_se_guarda(db):
    with pytest.raises(ErrorValidacion):
        crear_lote(db, "operador", {**LOTE, "cantidad": "-5"})
    assert db.execute("SELECT COUNT(*) FROM lotes").fetchone()[0] == 0


def test_codigo_repetido(db):
    crear_lote(db, "operador", LOTE)
    with pytest.raises(ErrorValidacion, match="Ya existe"):
        crear_lote(db, "operador", LOTE)
    assert db.execute("SELECT COUNT(*) FROM lotes").fetchone()[0] == 1
