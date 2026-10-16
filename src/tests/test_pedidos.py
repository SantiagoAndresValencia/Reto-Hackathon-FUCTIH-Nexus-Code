from conftest import ingresar, transformar

PEDIDO = {"kilos": "10", "comprador": "Tienda La Ceiba", "municipio": "Garzón", "direccion": "Calle 8 # 5-20",
          "telefono": "310 555 0101", "correo": "ceiba@ejemplo.co"}


def liberar(cliente, producto="P-CAC001-1", lote="CAC001"):
    ingresar(cliente, "operador")
    transformar(cliente, lote=lote)
    cliente.get("/logout")
    ingresar(cliente, "admin")
    cliente.post(f"/productos/{producto}/estado", data={"estado": "liberado", "motivo": "ok", "lote": lote})
    cliente.get("/logout")


def pedir(cliente, producto="P-CAC001-1", **cambios):
    return cliente.post(f"/ficha/{producto}/pedido", data={**PEDIDO, **cambios})


def test_ficha_muestra_precio_y_permite_pedir(cliente):
    liberar(cliente)
    ficha = cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)
    assert "25.000 COP/kg" in ficha and "Hacer un pedido" in ficha
    respuesta = pedir(cliente)
    assert respuesta.status_code == 302 and "/pedido/" in respuesta.headers["Location"]
    pagina = cliente.get(respuesta.headers["Location"]).get_data(as_text=True)
    assert "PED-0001" in pagina and "Esperando aprobación" in pagina and "250.000 COP" in pagina


def test_no_se_pide_producto_pendiente_ni_mas_de_lo_disponible(cliente):
    ingresar(cliente, "operador")
    transformar(cliente)
    cliente.get("/logout")
    assert "Hacer un pedido" not in cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)
    assert pedir(cliente).status_code == 400
    ingresar(cliente, "admin")
    cliente.post("/productos/P-CAC001-1/estado", data={"estado": "liberado", "motivo": "ok", "lote": "CAC001"})
    cliente.get("/logout")
    pedir(cliente, kilos="70")
    respuesta = pedir(cliente, kilos="20")
    assert respuesta.status_code == 400 and "Solo quedan 10 kg" in respuesta.get_data(as_text=True)


def test_comprador_cancela_con_razon_y_libera_kilos(cliente):
    liberar(cliente)
    enlace = pedir(cliente, kilos="80").headers["Location"].split("?")[0]
    token = enlace.rsplit("/", 1)[1]
    sin_razon = cliente.post(f"/pedido/{token}/cancelar", data={"motivo": " "}, follow_redirects=True)
    assert "Razón de la cancelación" in sin_razon.get_data(as_text=True)
    assert "Esperando aprobación" in sin_razon.get_data(as_text=True)
    cancelado = cliente.post(f"/pedido/{token}/cancelar", data={"motivo": "Ya no lo necesito"}, follow_redirects=True)
    assert "Pedido cancelado" in cancelado.get_data(as_text=True) and "Ya no lo necesito" in cancelado.get_data(as_text=True)
    assert pedir(cliente, kilos="80").status_code == 302


def test_admin_aprueba_o_rechaza_y_operador_no(cliente):
    liberar(cliente)
    token = pedir(cliente).headers["Location"].split("?")[0].rsplit("/", 1)[1]
    pedir(cliente, kilos="5")
    ingresar(cliente, "operador")
    assert cliente.get("/admin/pedidos").status_code == 403
    assert cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "aprobado", "motivo": "ok"}).status_code == 403
    cliente.get("/logout")
    ingresar(cliente, "admin")
    sin_motivo = cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "aprobado", "motivo": ""}, follow_redirects=True)
    assert "Motivo" in sin_motivo.get_data(as_text=True)
    cliente.post("/admin/pedidos/PED-0001/estado", data={"estado": "aprobado", "motivo": "Pago confirmado"})
    cliente.post("/admin/pedidos/PED-0002/estado", data={"estado": "rechazado", "motivo": "Sin transporte"})
    lista = cliente.get("/admin/pedidos").get_data(as_text=True)
    assert "Tienda La Ceiba" in lista and "Sin transporte" in lista
    auditoria = cliente.get("/admin/auditoria?q=PED-0001").get_data(as_text=True)
    assert "DENEGADO: pedido aprobado" in auditoria and "pedido aprobado (Pago confirmado)" in auditoria
    cliente.get("/logout")
    assert "Pedido aprobado" in cliente.get(f"/pedido/{token}").get_data(as_text=True)


def test_seguir_pedido_exige_el_contacto(cliente):
    liberar(cliente)
    pedir(cliente)
    bien = cliente.get("/pedidos/buscar?numero=ped-0001&contacto=CEIBA@ejemplo.co")
    assert "/pedido/" in bien.headers["Location"]
    mal = cliente.get("/pedidos/buscar?numero=PED-0001&contacto=otro@ejemplo.co", follow_redirects=True)
    assert "no coinciden" in mal.get_data(as_text=True)


def test_catalogo_muestra_disponible_y_no_expone_compradores(cliente):
    liberar(cliente)
    pedir(cliente, kilos="30")
    catalogo = cliente.get("/comprador").get_data(as_text=True)
    assert "50 kg" in catalogo
    for privado in ("Tienda La Ceiba", "ceiba@ejemplo.co", "310 555 0101", "Calle 8"):
        assert privado not in catalogo
        assert privado not in cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)


def test_pedido_exige_direccion_telefono_y_correo_validos(cliente):
    liberar(cliente)
    for campo, valor, mensaje in (("municipio", "Bogotá", "municipio del Huila"), ("municipio", "", "Municipio"),
                                  ("direccion", "", "Dirección de entrega"), ("telefono", "abc", "teléfono válido"),
                                  ("correo", "ceiba.co", "correo válido")):
        respuesta = pedir(cliente, **{campo: valor})
        assert respuesta.status_code == 400 and mensaje in respuesta.get_data(as_text=True)
    pagina = cliente.get(pedir(cliente).headers["Location"]).get_data(as_text=True)
    assert "Garzón, Huila" in pagina and "Calle 8 # 5-20" in pagina and "310 555 0101" in pagina and "ceiba@ejemplo.co" in pagina


def test_seguir_pedido_con_el_telefono(cliente):
    liberar(cliente)
    pedir(cliente)
    assert "/pedido/" in cliente.get("/pedidos/buscar?numero=PED-0001&contacto=3105550101").headers["Location"]


def test_migra_pedidos_con_contacto_unico(tmp_path, monkeypatch):
    import sqlite3
    from src import db
    ruta = tmp_path / "vieja.db"
    conn = sqlite3.connect(ruta)
    conn.executescript(db.RUTA_SCHEMA.read_text(encoding="utf-8").replace(
        "    municipio       TEXT NOT NULL CHECK (length(trim(municipio)) > 0),\n"
        "    direccion       TEXT NOT NULL CHECK (length(trim(direccion)) > 0),\n"
        "    telefono        TEXT NOT NULL CHECK (length(trim(telefono)) > 0),\n"
        "    correo          TEXT NOT NULL CHECK (correo LIKE '%_@_%._%'),\n",
        "    contacto        TEXT NOT NULL,\n"))
    conn.execute("INSERT INTO lotes (codigo, productor, origen, fecha_recepcion, cantidad, creado_por) "
                 "VALUES ('CAC001', 'P', 'Rivera', '2026-10-15', 100, 's')")
    conn.execute("INSERT INTO transformaciones (op_id, lote_codigo, etapa, responsable, fecha, entrada, salida, creado_por) "
                 "VALUES ('o', 'CAC001', 'Secado', 'r', '2026-10-15', 100, 80, 's')")
    conn.execute("INSERT INTO productos (codigo, transformacion_id, lote_codigo, nombre, cantidad, precio_venta, estado, motivo_estado) "
                 "VALUES ('P-CAC001-1', 1, 'CAC001', 'Cacao', 80, 25000, 'liberado', 'ok')")
    conn.execute("INSERT INTO pedidos (token, producto_codigo, comprador, contacto, kilos, precio_kg) "
                 "VALUES ('x' || hex(randomblob(10)), 'P-CAC001-1', 'Ceiba', 'ceiba@ejemplo.co', 5, 25000)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "RUTA_DB", ruta)
    db.crear_tablas()
    conn = sqlite3.connect(ruta)
    assert conn.execute("SELECT comprador, correo, telefono, municipio, direccion FROM pedidos").fetchone() == \
        ("Ceiba", "ceiba@ejemplo.co", "Sin registrar", "Sin registrar", "Sin registrar")
    assert conn.execute("SELECT disponible FROM v_producto_disponible").fetchone() == (75,)
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'trg_pedidos_%'").fetchone() == (5,)


def test_agrega_municipio_a_pedidos_existentes(tmp_path, monkeypatch):
    import sqlite3
    from src import db
    ruta = tmp_path / "sin_municipio.db"
    conn = sqlite3.connect(ruta)
    conn.executescript(db.RUTA_SCHEMA.read_text(encoding="utf-8").replace(
        "    municipio       TEXT NOT NULL CHECK (length(trim(municipio)) > 0),\n", ""))
    conn.close()
    monkeypatch.setattr(db, "RUTA_DB", ruta)
    db.crear_tablas()
    conn = sqlite3.connect(ruta)
    assert "municipio" in {c[1] for c in conn.execute("PRAGMA table_info(pedidos)")}


def test_lista_tiene_los_37_municipios_del_huila():
    from src.validaciones import MUNICIPIOS_HUILA
    assert len(set(MUNICIPIOS_HUILA)) == 37 and {"Neiva", "Pitalito", "San Agustín", "Íquira"} <= set(MUNICIPIOS_HUILA)
