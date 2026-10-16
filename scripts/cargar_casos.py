"""Registra 15 casos de prueba (CAC004-CAC018) en distintos estados, usando las mismas rutas que la web.

Uso (desde la raíz del repositorio, con la app detenida):
    flask --app src/app restaurar datos/respaldo_demo.db
    python scripts/cargar_casos.py
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db  # noqa: E402
from src.app import app  # noqa: E402

FECHA = "2026-10-16"


def entrar(cliente, usuario, clave):
    cliente.get("/logout")
    cliente.post("/login", data={"usuario": usuario, "clave": clave})


def lote(cliente, codigo, origen, kg, productor="Asociación demo"):
    cliente.post("/lotes/nuevo", data={"codigo": codigo, "productor": productor, "origen": origen,
                                       "fecha_recepcion": "2026-10-15", "cantidad": str(kg)})


def transformar(cliente, codigo, etapa, entrada, salida, costo, precio, producto="Cacao seco", justificacion=""):
    cliente.post(f"/lotes/{codigo}/transformar", data={
        "op_id": str(uuid.uuid4()), "etapa": etapa, "responsable": "Operador demo", "fecha": FECHA,
        "entrada": str(entrada), "salida": str(salida), "producto": producto, "costo_total": str(costo),
        "costos_incluidos": "Mano de obra, energía y transporte", "precio_venta": str(precio),
        "justificacion": justificacion})


def estado(cliente, producto, nuevo, motivo):
    cliente.post(f"/productos/{producto}/estado", data={"estado": nuevo, "motivo": motivo})


def pedir(producto, kilos, comprador):
    """Pedido hecho por un comprador sin sesión. Devuelve (número, token)."""
    with app.test_client() as c:
        r = c.post(f"/ficha/{producto}/pedido", data={
            "kilos": str(kilos), "comprador": comprador, "municipio": "Neiva", "direccion": "Calle 10 # 5-20",
            "telefono": "3101234567", "correo": "compras@ejemplo.co"})
        token = r.headers.get("Location", "").split("/pedido/")[-1].split("?")[0]
    fila = db.sqlite3.connect(db.RUTA_DB).execute("SELECT id FROM pedidos WHERE token = ?", (token,)).fetchone()
    return f"PED-{fila[0]:04d}", token


def decidir(cliente, numero, nuevo, motivo):
    cliente.post(f"/admin/pedidos/{numero}/estado", data={"estado": nuevo, "motivo": motivo})


db.crear_tablas()
con = db.sqlite3.connect(db.RUTA_DB)
if con.execute("SELECT 1 FROM usuarios WHERE usuario = 'admin'").fetchone() is None:
    sys.exit("ERROR: faltan los usuarios. Corre primero: flask --app src/app restaurar datos/respaldo_demo.db")
if con.execute("SELECT 1 FROM lotes WHERE codigo = 'CAC004'").fetchone():
    sys.exit("ERROR: los casos ya existen. Restaura primero: flask --app src/app restaurar datos/respaldo_demo.db")

app.config["TESTING"] = True
op = app.test_client()
entrar(op, "operador", "operador123")
adm = app.test_client()
entrar(adm, "admin", "admin123")

# 1. Recibido, sin transformar
lote(op, "CAC004", "Pitalito", 60)
# 2. Transformado a medias, producto pendiente
lote(op, "CAC005", "Garzón", 120)
transformar(op, "CAC005", "Fermentación", 70, 63, 700000, 15000, "Cacao fermentado")
# 3. Liberado, en catálogo
lote(op, "CAC006", "Gigante", 80)
transformar(op, "CAC006", "Secado", 80, 72, 1080000, 22000)
estado(adm, "P-CAC006-1", "liberado", "Calidad verificada por el comité")
# 4. Liberado con pedido pendiente
lote(op, "CAC007", "La Plata", 90)
transformar(op, "CAC007", "Tostión", 90, 81, 1458000, 26000, "Cacao tostado")
estado(adm, "P-CAC007-1", "liberado", "Tostión conforme")
pedir("P-CAC007-1", 20, "Chocolates del Sur")
# 5. Liberado con pedido aprobado
lote(op, "CAC008", "Rivera", 70)
transformar(op, "CAC008", "Descascarillado", 70, 63, 1134000, 27000, "Nibs de cacao")
estado(adm, "P-CAC008-1", "liberado", "Granulometría correcta")
numero, _ = pedir("P-CAC008-1", 30, "Tienda Café y Cacao")
decidir(adm, numero, "aprobado", "Pago confirmado")
# 6. Liberado con pedido rechazado
lote(op, "CAC009", "Campoalegre", 60)
transformar(op, "CAC009", "Molienda", 60, 54, 1080000, 30000, "Licor de cacao")
estado(adm, "P-CAC009-1", "liberado", "Análisis de laboratorio aprobado")
numero, _ = pedir("P-CAC009-1", 10, "Comprador sin datos de pago")
decidir(adm, numero, "rechazado", "No se pudo confirmar el pago")
# 7. Liberado con pedido cancelado por el comprador
lote(op, "CAC010", "Algeciras", 50)
transformar(op, "CAC010", "Secado", 50, 45, 675000, 22000)
estado(adm, "P-CAC010-1", "liberado", "Humedad dentro del rango")
_, token = pedir("P-CAC010-1", 15, "Panadería La Espiga")
with app.test_client() as c:
    c.post(f"/pedido/{token}/cancelar", data={"motivo": "Cambió la fecha de su evento"})
# 8. Liberado y agotado
lote(op, "CAC011", "Neiva", 40)
transformar(op, "CAC011", "Tostión", 40, 36, 648000, 26000, "Cacao tostado")
estado(adm, "P-CAC011-1", "liberado", "Tostión conforme")
numero, _ = pedir("P-CAC011-1", 36, "Exportadora Huila")
decidir(adm, numero, "aprobado", "Compra de todo el producto")
# 9. Un producto bloqueado
lote(op, "CAC012", "Tello", 50)
transformar(op, "CAC012", "Secado", 50, 44, 660000, 22000)
estado(adm, "P-CAC012-1", "bloqueado", "Moho detectado en la inspección")
# 10. Lote completo bloqueado (hora 12) con un pedido pendiente afectado
lote(op, "CAC013", "Baraya", 100)
transformar(op, "CAC013", "Fermentación", 50, 45, 450000, 15000, "Cacao fermentado")
transformar(op, "CAC013", "Secado", 50, 43, 645000, 22000)
estado(adm, "P-CAC013-2", "liberado", "Humedad dentro del rango")
pedir("P-CAC013-2", 10, "Chocolates del Sur")
adm.post("/lotes/CAC013/bloquear", data={"motivo": "Reclamo del comprador por sabor a humo"})
# 11. Merma alta (30 %)
lote(op, "CAC014", "Palermo", 50)
transformar(op, "CAC014", "Secado", 50, 35, 525000, 22000)
# 12. Salida 0 kg
lote(op, "CAC015", "Aipe", 20)
transformar(op, "CAC015", "Tostión", 20, 0, 80000, 26000, "Cacao tostado")
# 13. Costo mayor que el precio
lote(op, "CAC016", "Isnos", 30)
transformar(op, "CAC016", "Molienda", 30, 27, 945000, 30000, "Licor de cacao")
# 14. Tres etapas, lote consumido por completo
lote(op, "CAC017", "Suaza", 90)
transformar(op, "CAC017", "Fermentación", 30, 27, 270000, 15000, "Cacao fermentado")
transformar(op, "CAC017", "Secado", 30, 27, 405000, 22000)
transformar(op, "CAC017", "Tostión", 30, 27, 486000, 26000, "Cacao tostado")
# 15. Salida mayor que la entrada, con justificación
lote(op, "CAC018", "Timaná", 40)
transformar(op, "CAC018", "Secado", 40, 42, 600000, 22000,
            justificacion="Báscula recalibrada: la entrada se pesó con 2 kg de menos")

con = db.sqlite3.connect(db.RUTA_DB)
print(f"{'Lote':7} {'Recibido':>8} {'Disp.':>6}  Productos (estado)          Pedidos         Alertas")
for codigo, recibido, disponible in con.execute(
        "SELECT codigo, recibido, disponible FROM v_inventario_lote WHERE codigo BETWEEN 'CAC004' AND 'CAC018' ORDER BY codigo"):
    productos = ", ".join(f"{c} {e}" for c, e in con.execute(
        "SELECT codigo, estado FROM productos WHERE lote_codigo = ? ORDER BY codigo", (codigo,))) or "—"
    pedidos = ", ".join(e for (e,) in con.execute(
        "SELECT pe.estado FROM pedidos pe JOIN productos p ON p.codigo = pe.producto_codigo "
        "WHERE p.lote_codigo = ? ORDER BY pe.id", (codigo,))) or "—"
    alertas = con.execute("SELECT COUNT(*) FROM alertas WHERE lote_codigo = ?", (codigo,)).fetchone()[0]
    print(f"{codigo:7} {recibido:>8g} {disponible:>6g}  {productos:28} {pedidos:15} {alertas}")
total = con.execute("SELECT COUNT(*) FROM lotes WHERE codigo BETWEEN 'CAC004' AND 'CAC018'").fetchone()[0]
print(f"\nCasos registrados: {total} de 15")
