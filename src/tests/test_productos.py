from conftest import ingresar, transformar


def test_operador_no_puede_liberar(cliente):
    ingresar(cliente, "operador")
    transformar(cliente)
    respuesta = cliente.post("/productos/P-CAC001-1/estado",
                             data={"estado": "liberado", "motivo": "ok", "lote": "CAC001"})
    assert respuesta.status_code == 403
    assert "revisión" in cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)
    cliente.get("/logout")
    ingresar(cliente, "admin")
    assert "DENEGADO: cambiar estado" in cliente.get("/admin/auditoria").get_data(as_text=True)


def test_bloquear_se_ve_en_ficha_y_auditoria(cliente):
    ingresar(cliente, "operador")
    transformar(cliente)
    cliente.get("/logout")
    ingresar(cliente, "admin")
    cliente.post("/productos/P-CAC001-1/estado",
                 data={"estado": "bloqueado", "motivo": "Reclamo del comprador", "lote": "CAC001"})
    cliente.get("/logout")
    ficha = cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)
    assert "bloqueado" in ficha
    ingresar(cliente, "admin")
    auditoria = cliente.get("/admin/auditoria?q=P-CAC001-1").get_data(as_text=True)
    assert "pendiente" in auditoria and "bloqueado" in auditoria


def test_bloquear_sin_motivo_no_cambia(cliente):
    ingresar(cliente, "operador")
    transformar(cliente)
    cliente.get("/logout")
    ingresar(cliente, "admin")
    respuesta = cliente.post("/productos/P-CAC001-1/estado", data={"estado": "bloqueado", "motivo": "", "lote": "CAC001"},
                             follow_redirects=True)
    assert "Motivo" in respuesta.get_data(as_text=True)


def test_ficha_publica_sin_costos_ni_productor(cliente):
    ingresar(cliente, "operador")
    transformar(cliente)
    cliente.get("/logout")
    ficha = cliente.get("/ficha/P-CAC001-1").get_data(as_text=True)
    assert "Rivera" in ficha
    for privado in ("1600000", "1.600.000", "Productor A", "Mano de obra"):
        assert privado not in ficha


def test_csv_filtrado_por_origen(cliente):
    ingresar(cliente, "admin")
    lineas = cliente.get("/admin/exportar.csv?origen=Rivera").get_data(as_text=True).strip().splitlines()
    assert lineas[0].startswith("codigo,origen")
    assert len(lineas) == 2 and lineas[1].startswith("CAC001,Rivera")


def test_operador_no_exporta_csv(cliente):
    ingresar(cliente, "operador")
    assert cliente.get("/admin/exportar.csv").status_code == 403
