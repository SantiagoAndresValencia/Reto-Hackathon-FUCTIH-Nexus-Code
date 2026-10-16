import sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(_file_).resolve().parent))
from src import db
from src.app import app

print("Base de datos:", db.RUTA_DB)
db.crear_tablas()
c = app.test_client()
r = c.post("/login", data={"usuario": "admin", "clave": "admin123"})
with c.session_transaction() as s:
    if s.get("usuario") != "admin":
        sys.exit("ERROR: no pude entrar como admin/admin123. Corre primero: flask --app src/app cargar-demo")
print("1. Sesion de admin: OK")

con = db.sqlite3.connect(db.RUTA_DB)
if con.execute("SELECT 1 FROM lotes WHERE codigo='CAC100'").fetchone() is None:
    c.post("/lotes/nuevo", data={"codigo": "CAC100", "productor": "Prueba 100 registros", "origen": "Garzón",
                                 "fecha_recepcion": "2026-10-16", "cantidad": "1000"})
disp = con.execute("SELECT disponible FROM v_inventario_lote WHERE codigo='CAC100'").fetchone()
if disp is None:
    sys.exit("ERROR: no se pudo crear el lote CAC100.")
print("2. Lote CAC100 disponible:", disp[0], "kg")

antes = con.execute("SELECT COUNT(*) FROM transformaciones WHERE lote_codigo='CAC100'").fetchone()[0]
for i in range(antes, 100):
    c.post("/lotes/CAC100/transformar", data={
        "op_id": str(uuid.uuid4()), "etapa": f"Etapa {i + 1}", "responsable": "Prueba", "fecha": "2026-10-16",
        "entrada": "10", "salida": "8", "producto": "Cacao seco", "costo_total": "160000",
        "costos_incluidos": "Prueba", "precio_venta": "25000"})
total = con.execute("SELECT COUNT(*) FROM transformaciones WHERE lote_codigo='CAC100'").fetchone()[0]
print("3. Transformaciones en CAC100:", total)
print("Ahora: flask --app src/app run  y abre  http://127.0.0.1:5000/lotes/CAC100  (como admin)")