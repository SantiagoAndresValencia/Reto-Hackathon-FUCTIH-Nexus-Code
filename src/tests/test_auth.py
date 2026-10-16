from conftest import ingresar


def test_sin_sesion_redirige_al_login(cliente):
    respuesta = cliente.get("/lotes")
    assert respuesta.status_code == 302 and "/login" in respuesta.headers["Location"]


def test_clave_incorrecta(cliente):
    respuesta = cliente.post("/login", data={"usuario": "admin", "clave": "mala"})
    assert "incorrectos" in respuesta.get_data(as_text=True)


def test_login_correcto(cliente):
    assert ingresar(cliente, "operador").status_code == 302
    assert cliente.get("/lotes").status_code == 200


def test_operador_no_entra_a_auditoria_y_queda_registrado(cliente):
    ingresar(cliente, "operador")
    assert cliente.get("/admin/auditoria").status_code == 403
    cliente.get("/logout")
    ingresar(cliente, "admin")
    assert "DENEGADO" in cliente.get("/admin/auditoria").get_data(as_text=True)


def test_cookie_falsificada_con_clave_antigua_no_entra(cliente):
    from flask import Flask
    atacante = Flask("atacante")
    atacante.secret_key = "solo-para-desarrollo"
    galleta = atacante.session_interface.get_signing_serializer(atacante).dumps(
        {"usuario": "intruso", "rol": "admin"})
    cliente.set_cookie("session", galleta)
    assert cliente.get("/admin/auditoria").status_code == 302
