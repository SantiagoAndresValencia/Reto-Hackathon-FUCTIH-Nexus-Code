import sqlite3
from pathlib import Path

import pytest

RUTA_SCHEMA = Path(__file__).resolve().parent.parent / "schema.sql"


@pytest.fixture
def conn():
    """Base de datos en memoria, nueva para cada prueba."""
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(RUTA_SCHEMA.read_text(encoding="utf-8"))
    yield c
    c.close()



def _usuario(conn, nombre="ana", rol="operador"):
    conn.execute(
        "INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (?, 'hash', ?)",
        (nombre, rol),
    )


def _lote(conn, codigo="CAC001", cantidad=100):
    conn.execute(
        "INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
        "VALUES (?, 'Productor X', 'Rivera', '2026-10-15', ?, 'ana')",
        (codigo, cantidad),
    )


def _transformacion(conn, op_id="op-1", lote="CAC001", entrada=100, salida=80,
                    costo=1600000, costos_incluidos="mano de obra y secado",
                    justificacion=None):
    cur = conn.execute(
        "INSERT INTO transformaciones "
        "(op_id, lote_codigo, etapa, responsable, fecha, entrada, salida, costo_total, "
        " costos_incluidos, justificacion, creado_por) "
        "VALUES (?, ?, 'secado', 'ana', '2026-10-15', ?, ?, ?, ?, ?, 'ana')",
        (op_id, lote, entrada, salida, costo, costos_incluidos, justificacion),
    )
    return cur.lastrowid


def _producto(conn, tid, codigo="P-CAC001-1", lote="CAC001", estado="pendiente", motivo=None):
    conn.execute(
        "INSERT INTO productos "
        "(codigo, transformacion_id, lote_codigo, nombre, cantidad, precio_venta, estado, motivo_estado) "
        "VALUES (?, ?, ?, 'Cacao seco', 80, 25000, ?, ?)",
        (codigo, tid, lote, estado, motivo),
    )


def _alerta(conn, tid):
    conn.execute(
        "INSERT INTO alertas (lote_codigo, transformacion_id, tipo, regla, causa) "
        "VALUES ('CAC001', ?, 'merma', 'merma > 15 %', 'merma real 20 %')",
        (tid,),
    )



def test_existen_las_seis_tablas(conn):
    nombres = {f[0] for f in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    esperadas = {"usuarios", "lotes", "transformaciones", "productos", "alertas", "auditoria"}
    assert esperadas <= nombres


def test_inserciones_validas(conn):
    _usuario(conn)
    _lote(conn)
    tid = _transformacion(conn)
    _producto(conn, tid)
    _alerta(conn, tid)
    conn.execute(
        "INSERT INTO auditoria (usuario, accion, entidad, entidad_id) "
        "VALUES ('ana', 'crear', 'lote', 'CAC001')"
    )
    estado = conn.execute("SELECT estado FROM productos").fetchone()[0]
    assert estado == "pendiente"  



@pytest.mark.parametrize("cantidad", [-5, 0])
def test_lote_cantidad_no_positiva(conn, cantidad):
    with pytest.raises(sqlite3.IntegrityError):
        _lote(conn, cantidad=cantidad)


def test_lote_con_campo_obligatorio_vacio(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
            "VALUES ('CAC009', '   ', 'Rivera', '2026-10-15', 50, 'ana')"
        )



def test_rol_invalido(conn):
    with pytest.raises(sqlite3.IntegrityError):
        _usuario(conn, rol="superjefe")


def test_usuario_unico(conn):
    _usuario(conn, "ana")
    with pytest.raises(sqlite3.IntegrityError):
        _usuario(conn, "ana")


def test_op_id_unico(conn):
    _lote(conn)
    _transformacion(conn, op_id="op-1")
    with pytest.raises(sqlite3.IntegrityError):
        _transformacion(conn, op_id="op-1")


def test_transformacion_con_lote_inexistente(conn):
    with pytest.raises(sqlite3.IntegrityError):
        _transformacion(conn, lote="NO-EXISTE")


def test_producto_estado_invalido(conn):
    _lote(conn)
    tid = _transformacion(conn)
    with pytest.raises(sqlite3.IntegrityError):
        _producto(conn, tid, estado="vendido", motivo="x")



def test_salida_mayor_que_entrada_exige_justificacion(conn):
    _lote(conn)
    with pytest.raises(sqlite3.IntegrityError):
        _transformacion(conn, op_id="a", entrada=100, salida=120)
    _transformacion(conn, op_id="b", entrada=100, salida=120,
                    justificacion="adición de insumos")


def test_costo_exige_costos_incluidos(conn):
    _lote(conn)
    with pytest.raises(sqlite3.IntegrityError):
        _transformacion(conn, op_id="a", costo=1600000, costos_incluidos=None)
    _transformacion(conn, op_id="b", entrada=50, salida=40, costo=0, costos_incluidos=None)


def test_liberar_o_bloquear_exige_motivo(conn):
    _lote(conn)
    tid = _transformacion(conn)
    for estado, motivo in [("bloqueado", None), ("liberado", "  ")]:
        with pytest.raises(sqlite3.IntegrityError):
            _producto(conn, tid, estado=estado, motivo=motivo)
    _producto(conn, tid, estado="bloqueado", motivo="queja del comprador")



def test_no_se_consume_mas_de_lo_disponible(conn):
    _lote(conn, cantidad=100)
    with pytest.raises(sqlite3.IntegrityError, match="INVENTARIO_INSUFICIENTE"):
        _transformacion(conn, op_id="op-0", entrada=120, salida=100)
    _transformacion(conn, op_id="op-1", entrada=100, salida=80)
    with pytest.raises(sqlite3.IntegrityError, match="INVENTARIO_INSUFICIENTE"):
        _transformacion(conn, op_id="op-2", entrada=1, salida=1)


def test_reenvio_no_duplica_el_consumo(conn):
    _lote(conn, cantidad=100)
    _transformacion(conn, op_id="op-1", entrada=60, salida=50)
    with pytest.raises(sqlite3.IntegrityError, match="op_id"):
        _transformacion(conn, op_id="op-1", entrada=60, salida=50)
    consumido = conn.execute("SELECT SUM(entrada) FROM transformaciones").fetchone()[0]
    assert consumido == 60


def test_vista_inventario(conn):
    _lote(conn, "CAC001", 100)
    _lote(conn, "CAC002", 150)
    tid = _transformacion(conn, op_id="op-1", lote="CAC001", entrada=100, salida=80)
    _producto(conn, tid, estado="liberado", motivo="inspección aprobada")
    filas = {
        f[0]: f
        for f in conn.execute(
            "SELECT codigo, recibido, consumido, disponible, costo_total, estados "
            "FROM v_inventario_lote"
        )
    }
    assert filas["CAC001"] == ("CAC001", 100, 100, 0, 1600000, "liberado")
    assert filas["CAC002"] == ("CAC002", 150, 0, 150, 0, "sin producto")


def test_transformacion_no_se_edita_en_cantidades(conn):
    _lote(conn)
    _transformacion(conn)
    with pytest.raises(sqlite3.IntegrityError, match="TRANSFORMACION_INMUTABLE"):
        conn.execute("UPDATE transformaciones SET entrada = 10")


def test_lote_no_baja_de_lo_ya_consumido(conn):
    _lote(conn, cantidad=100)
    _transformacion(conn, entrada=80, salida=60)
    with pytest.raises(sqlite3.IntegrityError, match="LOTE_MENOR_QUE_CONSUMO"):
        conn.execute("UPDATE lotes SET cantidad = 70 WHERE codigo = 'CAC001'")
    conn.execute("UPDATE lotes SET cantidad = 90 WHERE codigo = 'CAC001'")  



def test_ficha_publica_no_expone_datos_internos(conn):
    columnas = [c[0] for c in conn.execute("SELECT * FROM v_ficha_publica LIMIT 0").description]
    for prohibida in ("costo", "productor", "responsable", "creado_por",
                      "motivo", "incidencias", "justificacion"):
        assert not any(prohibida in c for c in columnas), prohibida
    assert "origen" in columnas and "estado" in columnas


def test_ficha_publica_bloqueado_no_esta_en_venta(conn):
    _lote(conn)
    tid = _transformacion(conn)
    _producto(conn, tid, codigo="P-CAC001-1", estado="bloqueado", motivo="queja del comprador")
    _producto(conn, tid, codigo="P-CAC001-2", estado="liberado", motivo="inspección aprobada")
    fila = conn.execute(
        "SELECT estado, origen, lote_codigo FROM v_ficha_publica "
        "WHERE codigo_producto = 'P-CAC001-1'"
    ).fetchone()
    assert fila == ("bloqueado", "Rivera", "CAC001")  
    en_venta = dict(conn.execute("SELECT codigo_producto, en_venta FROM v_ficha_publica"))
    assert en_venta == {"P-CAC001-1": 0, "P-CAC001-2": 1}



def test_auditoria_es_solo_de_agregar(conn):
    conn.execute(
        "INSERT INTO auditoria (usuario, accion, entidad, entidad_id) "
        "VALUES ('ana', 'crear', 'lote', 'CAC001')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="AUDITORIA_INMUTABLE"):
        conn.execute("UPDATE auditoria SET accion = 'otra'")
    with pytest.raises(sqlite3.IntegrityError, match="AUDITORIA_INMUTABLE"):
        conn.execute("DELETE FROM auditoria")
    assert conn.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0] == 1


@pytest.mark.parametrize("tabla", ["productos", "alertas", "transformaciones", "lotes"])
def test_historial_no_se_borra(conn, tabla):
    _lote(conn)
    tid = _transformacion(conn)
    _producto(conn, tid)
    _alerta(conn, tid)
    with pytest.raises(sqlite3.IntegrityError, match="HISTORIAL_INMUTABLE"):
        conn.execute(f"DELETE FROM {tabla}")
    assert conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 1


def test_pedidos_no_sobrevenden_ni_se_reabren(conn):
    _lote(conn)
    tid = _transformacion(conn)
    _producto(conn, tid, codigo="P-CAC001-1", estado="pendiente")
    insertar = ("INSERT INTO pedidos (token, producto_codigo, comprador, contacto, kilos, precio_kg) "
                "VALUES (?, 'P-CAC001-1', 'C', 'c@x.co', ?, 1000)")
    with pytest.raises(sqlite3.IntegrityError, match="PRODUCTO_NO_DISPONIBLE"):
        conn.execute(insertar, ("t" * 20, 1))
    conn.execute("UPDATE productos SET estado = 'liberado', motivo_estado = 'ok' WHERE codigo = 'P-CAC001-1'")
    disponible = conn.execute("SELECT cantidad FROM productos WHERE codigo = 'P-CAC001-1'").fetchone()[0]
    conn.execute(insertar, ("a" * 20, disponible))
    with pytest.raises(sqlite3.IntegrityError, match="INVENTARIO_INSUFICIENTE"):
        conn.execute(insertar, ("b" * 20, 1))
    conn.execute("UPDATE pedidos SET estado = 'cancelado', motivo_estado = 'cambio' WHERE token = ?", ("a" * 20,))
    with pytest.raises(sqlite3.IntegrityError, match="PEDIDO_CERRADO"):
        conn.execute("UPDATE pedidos SET estado = 'aprobado', motivo_estado = 'x' WHERE token = ?", ("a" * 20,))
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        conn.execute(insertar.replace("'C'", "'C2'").replace("kilos, precio_kg)", "kilos, precio_kg, estado)")
                     .replace("1000)", "1000, 'rechazado')"), ("c" * 20, 1))
