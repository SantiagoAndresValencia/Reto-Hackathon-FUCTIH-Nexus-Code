import sqlite3
from pathlib import Path

import click

from src import db


def huella(ruta):
    if not Path(ruta).is_file():
        raise click.ClickException(f"No existe el archivo {ruta}")
    conn = sqlite3.connect(Path(ruta).resolve().as_uri() + "?mode=ro", uri=True)
    datos = {
        "integridad": conn.execute("PRAGMA integrity_check").fetchone()[0],
        "lotes": [r[0] for r in conn.execute("SELECT codigo FROM lotes ORDER BY codigo")],
        "total_recibido_kg": conn.execute("SELECT COALESCE(SUM(cantidad), 0) FROM lotes").fetchone()[0],
        "transformaciones": conn.execute("SELECT COUNT(*) FROM transformaciones").fetchone()[0],
        "productos": conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0],
        "auditoria": conn.execute("SELECT COUNT(*) FROM auditoria").fetchone()[0],
    }
    conn.close()
    return datos


def copiar(origen, destino):
    fuente, copia = sqlite3.connect(origen), sqlite3.connect(destino)
    fuente.backup(copia)
    fuente.close()
    copia.close()


def registrar_comandos(app):
    @app.cli.command("respaldar")
    @click.argument("destino", default="datos/respaldo.db")
    def respaldar(destino):
        copiar(db.RUTA_DB, destino)
        click.echo(f"Respaldo creado en {destino}: {huella(destino)}")

    @app.cli.command("restaurar")
    @click.argument("origen")
    def restaurar(origen):
        try:
            esperado = huella(origen)
        except sqlite3.DatabaseError:
            raise click.ClickException(f"{origen} no es un respaldo válido; no se tocó la base actual.") from None
        copiar(origen, db.RUTA_DB)
        obtenido = huella(db.RUTA_DB)
        click.echo(f"Esperado: {esperado}")
        click.echo(f"Obtenido: {obtenido}")
        click.echo("INTEGRIDAD OK" if esperado == obtenido else "ERROR: la restauración no coincide")