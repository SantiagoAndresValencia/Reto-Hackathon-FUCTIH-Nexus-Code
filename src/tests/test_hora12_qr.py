from src.tests.conftest import ingresar, transformar


def _dos_productos(cliente):
    ingresar(cliente, "operador")
    transformar(cliente, "CAC002", op_id="a", entrada="50", salida="45")
    transformar(cliente, "CAC002", op_id="b", entrada="50", salida="40")
    cliente.get("/logout")


def test_admin_bloquea_lote_completo_y_ve_kg_afectados(cliente):
    _dos_productos(cliente)
    ingresar(cliente, "admin")
    r = cliente.post("/lotes/CAC002/bloquear", data={"motivo": "Reclamo por humedad"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "2 producto(s), 85 kg afectados" in html
    for codigo in ("P-CAC002-1", "P-CAC002-2"):
        assert "Producto bloqueado" in cliente.get(f"/ficha/{codigo}").get_data(as_text=True)
    auditoria = cliente.get("/admin/auditoria?q=CAC002").get_data(as_text=True)
    assert "bloquear lote (Reclamo por humedad)" in auditoria


def test_operador_no_puede_bloquear_lote(cliente):
    _dos_productos(cliente)
    ingresar(cliente, "operador")
    assert cliente.post("/lotes/CAC002/bloquear", data={"motivo": "x"}).status_code == 403
    assert "Producto bloqueado" not in cliente.get("/ficha/P-CAC002-1").get_data(as_text=True)


def test_bloquear_lote_sin_motivo_no_cambia(cliente):
    _dos_productos(cliente)
    ingresar(cliente, "admin")
    r = cliente.post("/lotes/CAC002/bloquear", data={"motivo": " "}, follow_redirects=True)
    assert "Motivo" in r.get_data(as_text=True)
    assert "Producto bloqueado" not in cliente.get("/ficha/P-CAC002-1").get_data(as_text=True)


def test_etiqueta_qr_apunta_a_la_ficha(cliente):
    _dos_productos(cliente)
    ip = "http://192.168.1.203:5000"
    cliente.post("/login", data={"usuario": "operador", "clave": "operador123"}, base_url=ip)
    r = cliente.get("/productos/P-CAC002-1/etiqueta", base_url=ip)
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "<svg" in html
    assert "http://192.168.1.203:5000/ficha/P-CAC002-1" in html
    assert cliente.get("/productos/NO-EXISTE/etiqueta", base_url=ip).status_code == 404
