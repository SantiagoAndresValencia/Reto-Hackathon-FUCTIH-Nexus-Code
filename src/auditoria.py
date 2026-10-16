def registrar(db, usuario, accion, entidad, entidad_id, campo="", antes="", despues=""):
    """Registra una acción de auditoría en la base de datos."""
    db.execute(
        "INSERT INTO auditoria (usuario, accion, entidad, entidad_id, campo, valor_anterior, valor_nuevo) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (usuario, accion, entidad, entidad_id, campo, str(antes), str(despues)),
    )