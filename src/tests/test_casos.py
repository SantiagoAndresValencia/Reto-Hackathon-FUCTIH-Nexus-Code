import sqlite3

from conftest import ingresar
from test_pedidos import liberar, pedir

from src import db
from src.app import app


def test_quince_casos_cubren_todos_los_estados(cliente):
    salida = app.test_cli_runner().invoke(args=["cargar-casos"]).output
    assert "15 casos cargados" in salida, salida
    conn = sqlite3.connect(db.RUTA_DB)
    pedidos = dict(conn.execute("SELECT estado, COUNT(*) FROM pedidos GROUP BY estado").fetchall())
    assert pedidos == {"pendiente": 1, "aprobado": 1, "enviado": 2, "entregado": 3, "rechazado": 2, "cancelado": 2}
    productos = dict(conn.execute("SELECT estado, COUNT(*) FROM productos GROUP BY estado").fetchall())
    assert productos == {"pendiente": 2, "liberado": 10, "bloqueado": 2}
    assert conn.execute("SELECT COUNT(*) FROM lotes WHERE estados = 'sin producto'"
                        .replace("lotes", "v_inventario_lote")).fetchone()[0] >= 1
    assert {r[0] for r in conn.execute("SELECT tipo FROM alertas")} == {"merma", "costo"}
    assert conn.execute("SELECT COUNT(*) FROM auditoria WHERE accion LIKE 'DENEGADO%' AND usuario = 'operador'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM v_producto_disponible WHERE disponible <= 0").fetchone()[0] == 1
    # Cada pedido deja su rastro: la creación y un registro por cada cambio de estado, en orden
    pasos = {"pendiente": [], "aprobado": ["aprobado"], "enviado": ["aprobado", "enviado"],
             "entregado": ["aprobado", "enviado", "entregado"], "rechazado": ["rechazado"]}
    for numero, estado in conn.execute("SELECT printf('PED-%04d', id), estado FROM pedidos"):
        rastro = [r[0] for r in conn.execute("SELECT valor_nuevo FROM auditoria WHERE entidad = 'pedido' AND entidad_id = ? "
                                             "AND campo = 'estado' ORDER BY id", (numero,))]
        assert rastro in ([["cancelado"], ["aprobado", "cancelado"]] if estado == "cancelado" else [pasos[estado]]), numero
    assert "ya estaban cargados" in app.test_cli_runner().invoke(args=["cargar-casos"]).output
    assert conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0] == 11


def test_ciclo_completo_aprobado_enviado_entregado(cliente):
    liberar(cliente)
    token = pedir(cliente).headers["Location"].split("?")[0].rsplit("/", 1)[1]
    ingresar(cliente, "admin")
    saltar = cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "enviado", "motivo": "guía 1"}, follow_redirects=True)
    assert "no se puede pasar a enviado" in saltar.get_data(as_text=True)
    cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "aprobado", "motivo": "Pago confirmado"})
    cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "enviado", "motivo": "Guía 4471"})
    cliente.get("/logout")
    pagina = cliente.get(f"/pedido/{token}").get_data(as_text=True)
    assert "Pedido enviado" in pagina and "Guía 4471" in pagina and "Confirmar que lo recibí" in pagina
    assert "Cancelar el pedido" not in pagina
    no_cancela = cliente.post(f"/pedido/{token}/cancelar", data={"motivo": "ya no"}, follow_redirects=True)
    assert "no se puede cancelar" in no_cancela.get_data(as_text=True)
    final = cliente.post(f"/pedido/{token}/recibido", data={"comentario": "Llegó bien"}, follow_redirects=True).get_data(as_text=True)
    assert "Pedido entregado" in final and "Historial del pedido" in final and "Llegó bien" in final
    # Entregado es final y los kilos siguen descontados del producto
    conn = sqlite3.connect(db.RUTA_DB)
    assert conn.execute("SELECT disponible FROM v_producto_disponible WHERE codigo = 'P-CAC001-1'").fetchone() == (70,)
    ingresar(cliente, "admin")
    otra = cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "rechazado", "motivo": "x"}, follow_redirects=True)
    assert "no se puede pasar a rechazado" in otra.get_data(as_text=True)


def test_no_se_envia_un_producto_bloqueado(cliente):
    liberar(cliente)
    pedir(cliente)
    ingresar(cliente, "admin")
    cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "aprobado", "motivo": "ok"})
    cliente.post("/productos/P-CAC001-1/estado", data={"estado": "bloqueado", "motivo": "humedad", "lote": "CAC001"})
    r = cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "enviado", "motivo": "guía"}, follow_redirects=True)
    assert "libérelo antes de enviar" in r.get_data(as_text=True)


def test_migra_pedidos_sin_estados_de_envio(tmp_path, monkeypatch):
    ruta = tmp_path / "vieja.db"
    conn = sqlite3.connect(ruta)
    conn.executescript(db.RUTA_SCHEMA.read_text(encoding="utf-8").replace("'enviado', 'entregado', ", ""))
    conn.execute("INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
                 "VALUES ('CAC001', 'P', 'Rivera', '2026-10-15', 100, 's')")
    conn.execute("INSERT INTO transformaciones (op_id, lote_codigo, etapa, responsable, fecha, entrada, salida, creado_por) "
                 "VALUES ('o', 'CAC001', 'Secado', 'r', '2026-10-15', 100, 80, 's')")
    conn.execute("INSERT INTO productos (codigo, transformacion_id, lote_codigo, nombre, cantidad, precio_venta, estado, motivo_estado) "
                 "VALUES ('P-CAC001-1', 1, 'CAC001', 'Cacao', 80, 25000, 'liberado', 'ok')")
    conn.execute("INSERT INTO pedidos (token, producto_codigo, comprador, municipio, direccion, telefono, correo, kilos, "
                 "precio_kg, estado, motivo_estado) VALUES ('x' || hex(randomblob(10)), 'P-CAC001-1', 'Ceiba', 'Neiva', "
                 "'Calle 1', '3100000000', 'c@x.co', 5, 25000, 'aprobado', 'ok')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "RUTA_DB", ruta)
    db.crear_tablas()
    conn = sqlite3.connect(ruta)
    conn.execute("UPDATE pedidos SET estado = 'enviado', motivo_estado = 'guía' WHERE id = 1")
    assert conn.execute("SELECT estado, comprador FROM pedidos").fetchone() == ("enviado", "Ceiba")
    assert conn.execute("SELECT disponible FROM v_producto_disponible").fetchone() == (75,)
