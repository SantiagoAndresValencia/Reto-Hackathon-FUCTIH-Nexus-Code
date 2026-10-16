"""15 casos de demostración ejecutados por las mismas rutas que usan las personas.

Cada caso pasa por el operador (recibe y transforma), el administrador (libera, bloquea, aprueba, envía)
y el comprador (pide, cancela, confirma la entrega). Así la auditoría, las alertas y los estados quedan
igual que si alguien lo hubiera hecho a mano. Uso: flask --app src.app cargar-casos
"""
import uuid

import click

from src.db import obtener_db

MARCA = "Finca El Mirador"  # productor del caso 1: si ya existe, los casos están cargados

COMPRADORES = {
    "rosa": ("Chocolates Doña Rosa", "Neiva", "Calle 10 # 4-21, Centro", "310 456 7812", "compras@donarosa.ejemplo.co"),
    "ceiba": ("Tienda La Ceiba", "Garzón", "Carrera 9 # 6-40, barrio Las Ceibas", "311 220 4410", "pedidos@laceiba.ejemplo.co"),
    "paraiso": ("Café y Cacao El Paraíso", "Pitalito", "Calle 5 # 3-18, Centro", "312 870 1133", "hola@elparaiso.ejemplo.co"),
    "roque": ("Panadería San Roque", "La Plata", "Carrera 4 # 2-55", "313 640 2290", "sanroque@ejemplo.co"),
    "sur": ("Cooperativa Sabores del Sur", "Pitalito", "Vereda Charguayaco, bodega 2", "314 502 7781", "compras@saboresdelsur.ejemplo.co"),
    "opita": ("Restaurante Tierra Opita", "Neiva", "Avenida La Toma # 12-30", "315 309 6620", "cocina@tierraopita.ejemplo.co"),
    "andaquies": ("Heladería Los Andaquíes", "San Agustín", "Calle 3 # 11-07, Centro", "316 118 4045", "helados@andaquies.ejemplo.co"),
    "dulce": ("Repostería Dulce Huila", "Campoalegre", "Carrera 7 # 18-02", "317 455 9036", "ventas@dulcehuila.ejemplo.co"),
}


class Ejecutor:
    """Clientes con sesión para cada persona y atajos para cada acción de la app."""

    def __init__(self, app):
        self.operador = self._sesion(app, "operador", "operador123")
        self.admin = self._sesion(app, "admin", "admin123")
        self.comprador = app.test_client()
        self.app = app

    @staticmethod
    def _sesion(app, usuario, clave):
        cliente = app.test_client()
        if cliente.post("/login", data={"usuario": usuario, "clave": clave}).status_code != 302:
            raise click.ClickException(f"No se pudo ingresar como {usuario}. Ejecute antes: flask --app src.app cargar-demo")
        return cliente

    @staticmethod
    def _revisar(respuesta, esperado, que):
        texto = respuesta.get_data(as_text=True)
        if esperado not in texto:
            raise click.ClickException(f"Falló «{que}»: la app no respondió «{esperado}».")
        return texto

    def lote(self, codigo, productor, origen, fecha, kilos):
        r = self.operador.post("/lotes/nuevo", data={"codigo": codigo, "productor": productor, "origen": origen,
                                                     "fecha_recepcion": fecha, "cantidad": str(kilos)})
        self._revisar(r, f"{codigo} guardado", f"recibir {codigo}")
        return codigo

    def transformar(self, lote, etapa, fecha, entrada, salida, costo, precio, producto, incidencias="", costos="Mano de obra, energía y transporte"):
        r = self.operador.post(f"/lotes/{lote}/transformar", data={
            "op_id": str(uuid.uuid4()), "etapa": etapa, "responsable": "operador", "fecha": fecha,
            "producto": producto, "entrada": str(entrada), "salida": str(salida), "costo_total": str(costo),
            "costos_incluidos": costos if costo else "", "precio_venta": str(precio), "incidencias": incidencias})
        self._revisar(r, "Transformación registrada", f"transformar {lote}")

    def producto(self, codigo, estado, motivo, quien="admin"):
        cliente = self.admin if quien == "admin" else self.operador
        lote = codigo.split("-")[1]
        r = cliente.post(f"/productos/{codigo}/estado", data={"estado": estado, "motivo": motivo, "lote": lote})
        if quien == "admin" and "error=" in r.headers.get("Location", ""):
            raise click.ClickException(f"Falló «{estado} {codigo}».")
        return r.status_code

    def pedir(self, producto, kilos, quien):
        nombre, municipio, direccion, telefono, correo = COMPRADORES[quien]
        r = self.comprador.post(f"/ficha/{producto}/pedido", data={
            "kilos": str(kilos), "comprador": nombre, "municipio": municipio, "direccion": direccion,
            "telefono": telefono, "correo": correo})
        if r.status_code != 302:
            raise click.ClickException(f"Falló el pedido de {kilos} kg de {producto}.")
        token = r.headers["Location"].split("/pedido/")[1].split("?")[0]
        with self.app.app_context():
            numero = obtener_db().execute("SELECT printf('PED-%04d', id) FROM pedidos WHERE token = ?", (token,)).fetchone()[0]
        return numero, token

    def pedido(self, numero, estado, motivo):
        r = self.admin.post(f"/admin/pedidos/{numero}/estado", data={"estado": estado, "motivo": motivo})
        if "error=" in r.headers.get("Location", ""):
            raise click.ClickException(f"Falló «{estado} {numero}».")

    def cancelar(self, token, motivo):
        r = self.comprador.post(f"/pedido/{token}/cancelar", data={"motivo": motivo}, follow_redirects=True)
        self._revisar(r, "Pedido cancelado", "cancelar pedido")

    def recibido(self, token, nota):
        r = self.comprador.post(f"/pedido/{token}/recibido", data={"comentario": nota}, follow_redirects=True)
        self._revisar(r, "Pedido entregado", "confirmar entrega")


def _siguientes_codigos(db, cuantos):
    usados = {r[0] for r in db.execute("SELECT codigo FROM lotes")}
    codigos, n = [], 1
    while len(codigos) < cuantos:
        codigo = f"CAC{n:03d}"
        if codigo not in usados:
            codigos.append(codigo)
        n += 1
    return codigos


def cargar_casos(app):
    with app.app_context():
        db = obtener_db()
        if db.execute("SELECT 1 FROM lotes WHERE productor = ?", (MARCA,)).fetchone():
            return None
        c = _siguientes_codigos(db, 15)
    e = Ejecutor(app)
    casos = []

    def caso(numero, titulo, lote, producto="", pedido=""):
        casos.append((numero, titulo, lote, producto, pedido))

    # 1. Lote recibido que aún espera turno de proceso
    e.lote(c[0], MARCA, "Acevedo", "2026-10-14", 120)
    caso(1, "Recibido, sin transformar", c[0])

    # 2. Fermentación dentro de lo ideal, esperando la revisión del administrador
    e.lote(c[1], "Finca Las Brisas", "Garzón", "2026-10-02", 150)
    e.transformar(c[1], "Fermentación", "2026-10-09", 150, 132, 1_320_000, 15_000, "Cacao fermentado")
    caso(2, "Producto en revisión", c[1], f"P-{c[1]}-1")

    # 3. Secado con merma alta: alerta de merma y sigue en revisión
    e.lote(c[2], "Finca El Recreo", "La Plata", "2026-10-01", 100)
    e.transformar(c[2], "Secado", "2026-10-08", 100, 78, 1_560_000, 30_000, "Cacao seco",
                  incidencias="Lluvias durante tres días del secado")
    caso(3, "Merma alta (22 %) con alerta, en revisión", c[2], f"P-{c[2]}-1")

    # 4. Costo por encima del precio: alerta de costo y el administrador bloquea
    e.lote(c[3], "Finca Villa Luz", "Gigante", "2026-09-28", 90)
    e.transformar(c[3], "Tostión", "2026-10-06", 90, 80, 2_000_000, 24_000, "Cacao tostado")
    e.producto(f"P-{c[3]}-1", "bloqueado", "El precio no cubre el costo: recalcular antes de vender")
    caso(4, "Costo mayor que el precio, bloqueado", c[3], f"P-{c[3]}-1")

    # 5. Liberado y disponible, todavía sin pedidos
    e.lote(c[4], "Finca Monte Verde", "San Agustín", "2026-09-30", 110)
    e.transformar(c[4], "Secado", "2026-10-07", 110, 96, 1_440_000, 22_000, "Cacao seco")
    e.producto(f"P-{c[4]}-1", "liberado", "Humedad 7 % y grano sano en el control de calidad")
    caso(5, "Liberado, sin pedidos", c[4], f"P-{c[4]}-1")

    # 6. Pedido esperando aprobación
    e.lote(c[5], "Finca La Primavera", "Pitalito", "2026-09-29", 130)
    e.transformar(c[5], "Secado", "2026-10-06", 130, 112, 1_680_000, 22_000, "Cacao seco")
    e.producto(f"P-{c[5]}-1", "liberado", "Control de calidad aprobado")
    n6, _ = e.pedir(f"P-{c[5]}-1", 25, "rosa")
    caso(6, "Pedido pendiente de aprobación", c[5], f"P-{c[5]}-1", n6)

    # 7. Pedido aprobado, listo para despachar
    e.lote(c[6], "Finca El Encanto", "Timaná", "2026-09-27", 100)
    e.transformar(c[6], "Fermentación", "2026-10-03", 100, 90, 1_080_000, 18_000, "Cacao fermentado")
    e.producto(f"P-{c[6]}-1", "liberado", "Fermentación completa, corte de prueba aprobado")
    n7, _ = e.pedir(f"P-{c[6]}-1", 30, "ceiba")
    e.pedido(n7, "aprobado", "Pago confirmado por transferencia")
    caso(7, "Pedido aprobado, por enviar", c[6], f"P-{c[6]}-1", n7)

    # 8. Pedido enviado, en camino al comprador
    e.lote(c[7], "Finca Buenos Aires", "Suaza", "2026-09-25", 120)
    e.transformar(c[7], "Secado", "2026-10-02", 120, 104, 1_560_000, 23_000, "Cacao seco")
    e.producto(f"P-{c[7]}-1", "liberado", "Control de calidad aprobado")
    n8, _ = e.pedir(f"P-{c[7]}-1", 40, "paraiso")
    e.pedido(n8, "aprobado", "Pago contra entrega acordado por teléfono")
    e.pedido(n8, "enviado", "Coordinadora, guía 4471-2290, salió de Suaza el 15 de octubre")
    caso(8, "Pedido enviado, en camino", c[7], f"P-{c[7]}-1", n8)

    # 9. Pedido entregado: el comprador confirma que le llegó
    e.lote(c[8], "Finca La Esmeralda", "Palermo", "2026-09-22", 80)
    e.transformar(c[8], "Tostión", "2026-09-30", 80, 70, 1_260_000, 28_000, "Cacao tostado")
    e.producto(f"P-{c[8]}-1", "liberado", "Tueste uniforme, catación aprobada")
    n9, t9 = e.pedir(f"P-{c[8]}-1", 20, "roque")
    e.pedido(n9, "aprobado", "Pago confirmado")
    e.pedido(n9, "enviado", "Envía, guía 88213, entrega en La Plata")
    e.recibido(t9, "Llegó completo y en buen estado")
    caso(9, "Pedido entregado, confirmado por el comprador", c[8], f"P-{c[8]}-1", n9)

    # 10. Pedido rechazado por el administrador
    e.lote(c[9], "Finca El Porvenir", "Tello", "2026-09-26", 95)
    e.transformar(c[9], "Secado", "2026-10-04", 95, 83, 1_245_000, 22_000, "Cacao seco")
    e.producto(f"P-{c[9]}-1", "liberado", "Control de calidad aprobado")
    n10, _ = e.pedir(f"P-{c[9]}-1", 50, "opita")
    e.pedido(n10, "rechazado", "No hay transporte disponible a Neiva esta semana")
    caso(10, "Pedido rechazado por la asociación", c[9], f"P-{c[9]}-1", n10)

    # 11. El comprador cancela mientras su pedido estaba pendiente
    e.lote(c[10], "Finca San Isidro", "Íquira", "2026-09-24", 70)
    e.transformar(c[10], "Fermentación", "2026-10-01", 70, 63, 756_000, 18_000, "Cacao fermentado")
    e.producto(f"P-{c[10]}-1", "liberado", "Fermentación completa")
    n11, t11 = e.pedir(f"P-{c[10]}-1", 15, "andaquies")
    e.cancelar(t11, "Me equivoqué en la cantidad; haré un pedido nuevo")
    caso(11, "Cancelado por el comprador (pendiente)", c[10], f"P-{c[10]}-1", n11)

    # 12. El comprador cancela después de la aprobación, antes del envío
    e.lote(c[11], "Finca La Cabaña", "Oporapa", "2026-09-23", 100)
    e.transformar(c[11], "Secado", "2026-09-30", 100, 88, 1_320_000, 22_000, "Cacao seco")
    e.producto(f"P-{c[11]}-1", "liberado", "Control de calidad aprobado")
    n12, t12 = e.pedir(f"P-{c[11]}-1", 35, "dulce")
    e.pedido(n12, "aprobado", "Pago confirmado")
    e.cancelar(t12, "Nuestro cliente final canceló el encargo")
    caso(12, "Cancelado por el comprador (aprobado)", c[11], f"P-{c[11]}-1", n12)

    # 13. Producto agotado: un pedido entregado y otro enviado cubren todo el inventario
    e.lote(c[12], "Finca Alto Bonito", "Isnos", "2026-09-20", 60)
    e.transformar(c[12], "Molienda", "2026-09-29", 60, 52, 1_352_000, 38_000, "Pasta de cacao")
    e.producto(f"P-{c[12]}-1", "liberado", "Textura y acidez dentro de la ficha técnica")
    a13, _ = e.pedir(f"P-{c[12]}-1", 30, "sur")
    e.pedido(a13, "aprobado", "Cliente frecuente, pago a 15 días")
    e.pedido(a13, "enviado", "Vehículo de la asociación, salió el 10 de octubre")
    e.pedido(a13, "entregado", "Recibió Marta Ríos en la bodega de la cooperativa")
    b13, _ = e.pedir(f"P-{c[12]}-1", 22, "rosa")
    e.pedido(b13, "aprobado", "Pago confirmado")
    e.pedido(b13, "enviado", "Coordinadora, guía 4471-3105")
    caso(13, "Agotado (entregado + enviado)", c[12], f"P-{c[12]}-1", f"{a13}, {b13}")

    # 14. Liberado y luego bloqueado por calidad: el pedido en espera se rechaza
    e.lote(c[13], "Finca Los Naranjos", "Tarqui", "2026-09-21", 100)
    e.transformar(c[13], "Secado", "2026-09-28", 100, 85, 1_275_000, 22_000, "Cacao seco")
    e.producto(f"P-{c[13]}-1", "liberado", "Control de calidad inicial aprobado")
    n14, _ = e.pedir(f"P-{c[13]}-1", 20, "ceiba")
    e.producto(f"P-{c[13]}-1", "bloqueado", "Recontrol: humedad 9 %, por encima del 7 % permitido")
    e.pedido(n14, "rechazado", "El producto quedó bloqueado por humedad; le avisaremos del próximo lote")
    caso(14, "Liberado y luego bloqueado; pedido rechazado", c[13], f"P-{c[13]}-1", n14)

    # 15. Dos etapas (una perdida), el operador intenta liberar sin permiso y el administrador entrega
    e.lote(c[14], "Finca Santa Helena", "Santa María", "2026-09-18", 140)
    e.transformar(c[14], "Fermentación", "2026-09-25", 80, 72, 864_000, 18_000, "Cacao fermentado")
    e.transformar(c[14], "Secado", "2026-09-26", 60, 0, 120_000, 18_000, "Cacao seco",
                  incidencias="Se mojó el grano en el secadero; no hubo salida vendible")
    e.producto(f"P-{c[14]}-1", "liberado", "Intento del operador sin permiso", quien="operador")
    e.producto(f"P-{c[14]}-1", "liberado", "Fermentación completa, corte de prueba aprobado")
    n15, _ = e.pedir(f"P-{c[14]}-1", 10, "opita")
    e.pedido(n15, "aprobado", "Pago confirmado")
    e.pedido(n15, "enviado", "Vehículo de la asociación")
    e.pedido(n15, "entregado", "Entregado en la cocina del restaurante, recibió el chef")
    caso(15, "Dos etapas, intento denegado y entrega", c[14], f"P-{c[14]}-1", n15)
    return casos


def registrar_comando(app):
    @app.cli.command("cargar-casos")
    def cargar_casos_comando():
        """Ejecuta los 15 casos de demostración por las rutas de la app."""
        casos = cargar_casos(app)
        if casos is None:
            click.echo("Los 15 casos ya estaban cargados: no se repitió nada.")
            return
        with app.app_context():
            db = obtener_db()
            for numero, titulo, lote, producto, pedidos in casos:
                estado = db.execute("SELECT estado FROM productos WHERE codigo = ?", (producto,)).fetchone()
                estados = ", ".join(r[0] for r in db.execute(
                    "SELECT estado FROM pedidos WHERE producto_codigo = ? ORDER BY id", (producto,))) if pedidos else ""
                click.echo(f"{numero:>2}. {lote}  {titulo:<48} {producto or '—':<12} "
                           f"{estado[0] if estado else 'sin producto':<11} {pedidos} {('(' + estados + ')') if estados else ''}")
        click.echo("Listo: 15 casos cargados con su auditoría.")
