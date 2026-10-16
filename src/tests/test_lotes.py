import sqlite3
from pathlib import Path

import pytest

from src.lotes import crear_lote, disponible, registrar_transformacion
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


TRANSFORMACION = {"op_id": "op-1", "etapa": "Secado", "responsable": "operador", "fecha": "2026-10-15",
                  "entrada": "100", "salida": "80", "producto": "Cacao seco", "costo_total": "1600000",
                  "costos_incluidos": "Mano de obra y energía", "precio_venta": "25000"}


@pytest.fixture
def db_con_cac001(db):
    crear_lote(db, "operador", {**LOTE, "codigo": "CAC001", "cantidad": "100"})
    return db


def test_transformacion_crea_producto_y_alerta_de_merma(db_con_cac001):
    db = db_con_cac001
    assert registrar_transformacion(db, "operador", "CAC001", TRANSFORMACION) == "registrada"
    assert disponible(db, "CAC001")["disponible"] == 0
    producto = db.execute("SELECT * FROM productos").fetchone()
    assert (producto["codigo"], producto["cantidad"], producto["estado"]) == ("P-CAC001-1", 80, "pendiente")
    alerta = db.execute("SELECT * FROM alertas WHERE tipo = 'merma'").fetchone()
    assert "20" in alerta["causa"]


def test_no_consume_mas_de_lo_disponible(db_con_cac001):
    db = db_con_cac001
    with pytest.raises(ErrorValidacion, match="No hay suficiente"):
        registrar_transformacion(db, "operador", "CAC001", {**TRANSFORMACION, "entrada": "120"})
    assert disponible(db, "CAC001")["disponible"] == 100
    assert db.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0


def test_reenvio_no_consume_dos_veces(db_con_cac001):
    db = db_con_cac001
    datos = {**TRANSFORMACION, "entrada": "40", "salida": "35"}
    assert registrar_transformacion(db, "operador", "CAC001", datos) == "registrada"
    assert registrar_transformacion(db, "operador", "CAC001", datos) == "repetida"
    assert disponible(db, "CAC001")["disponible"] == 60


def test_salida_cero_no_crea_producto(db_con_cac001):
    db = db_con_cac001
    registrar_transformacion(db, "operador", "CAC001", {**TRANSFORMACION, "salida": "0"})
    assert db.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM alertas WHERE tipo = 'costo'").fetchone()[0] == 1


def test_salida_mayor_exige_justificacion(db_con_cac001):
    with pytest.raises(ErrorValidacion, match="justificación"):
        registrar_transformacion(db_con_cac001, "operador", "CAC001", {**TRANSFORMACION, "salida": "110"})
