"""Mide la consulta de trazabilidad con 100 transformaciones sintéticas en una base temporal.

Uso (desde la raíz del repositorio):  python scripts/medir_rendimiento.py
No toca datos/cacao.db.
"""
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db  # noqa: E402

db.RUTA_DB = Path(tempfile.mkdtemp()) / "rendimiento.db"

from src.app import app  # noqa: E402

REGISTROS = 100
REPETICIONES = 20

db.crear_tablas()
app.config["TESTING"] = True
app.test_cli_runner().invoke(args=["cargar-demo"])
cliente = app.test_client()
cliente.post("/login", data={"usuario": "admin", "clave": "admin123"})
cliente.post("/lotes/nuevo", data={"codigo": "CAC100", "productor": "Sintético", "origen": "Garzón",
                                   "fecha_recepcion": "2026-10-15", "cantidad": str(REGISTROS * 10)})
for i in range(REGISTROS):
    cliente.post("/lotes/CAC100/transformar", data={
        "op_id": f"rend-{i}", "etapa": f"Etapa {i + 1}", "responsable": "Script", "fecha": "2026-10-15",
        "entrada": "10", "salida": "8", "producto": "Cacao seco", "costo_total": "160000",
        "costos_incluidos": "Sintético", "precio_venta": "25000"})

con = db.sqlite3.connect(db.RUTA_DB)
conteo = {t: con.execute(f"SELECT COUNT(*) FROM {t} WHERE lote_codigo = 'CAC100'").fetchone()[0]
          for t in ("transformaciones", "productos", "alertas")}
con.close()

tiempos = []
for _ in range(REPETICIONES):
    inicio = time.perf_counter()
    respuesta = cliente.get("/lotes/CAC100")
    tiempos.append(time.perf_counter() - inicio)
    assert respuesta.status_code == 200 and "P-CAC100-100" in respuesta.get_data(as_text=True)

print(f"Equipo: {platform.system()} {platform.release()} · {platform.machine()} · Python {platform.python_version()}")
print(f"Registros del lote CAC100: {conteo}")
print(f"Consulta: GET /lotes/CAC100 (trazabilidad completa como admin), {REPETICIONES} repeticiones")
print(f"Primera: {tiempos[0]:.3f} s · Mediana: {statistics.median(tiempos):.3f} s · Máxima: {max(tiempos):.3f} s")
print("RESULTADO:", "CUMPLE (≤ 3 s)" if max(tiempos) <= 3 else "NO CUMPLE (> 3 s)")
