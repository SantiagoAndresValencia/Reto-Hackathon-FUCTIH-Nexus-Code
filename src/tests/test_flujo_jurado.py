from conftest import ingresar, transformar

from src import db
from src.respaldo import copiar, huella


def test_flujo_completo_del_jurado(cliente):
    ingresar(cliente, "operador")
    assert "CAC004 guardado" in cliente.post("/lotes/nuevo", data={
        "codigo": "CAC004", "productor": "Productor D", "origen": "Neiva",
        "fecha_recepcion": "2026-10-15", "cantidad": "50"}).get_data(as_text=True)
    assert "registrada" in transformar(cliente).get_data(as_text=True)
    cliente.get("/logout")

    ingresar(cliente, "admin")
    detalle = cliente.get("/lotes/CAC001").get_data(as_text=True)
    assert "20.0 %" in detalle and "20.000 COP/kg" in detalle and "Merma de 20 %" in detalle


def test_respaldo_y_restauracion(cliente, tmp_path):
    ingresar(cliente, "operador")
    transformar(cliente)
    antes = huella(db.RUTA_DB)
    copiar(db.RUTA_DB, tmp_path / "respaldo.db")
    transformar(cliente, lote="CAC002", entrada="10", salida="9")
    copiar(tmp_path / "respaldo.db", db.RUTA_DB)
    assert huella(db.RUTA_DB) == antes
