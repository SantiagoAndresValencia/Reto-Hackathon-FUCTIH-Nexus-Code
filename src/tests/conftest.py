import pytest

from src import db
from src.app import app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "RUTA_DB", tmp_path / "prueba.db")
    db.crear_tablas()
    app.config["TESTING"] = True
    app.test_cli_runner().invoke(args=["cargar-demo"])
    return app.test_client()


def ingresar(cliente, usuario):
    claves = {"operador": "operador123", "admin": "admin123"}
    return cliente.post("/login", data={"usuario": usuario, "clave": claves[usuario]})


def transformar(cliente, lote="CAC001", **cambios):
    datos = {"op_id": f"op-{lote}", "etapa": "Secado", "responsable": "operador", "fecha": "2026-10-15",
             "entrada": "100", "salida": "80", "producto": "Cacao seco", "costo_total": "1600000",
             "costos_incluidos": "Mano de obra y energía", "precio_venta": "25000"}
    datos.update(cambios)
    return cliente.post(f"/lotes/{lote}/transformar", data=datos)
