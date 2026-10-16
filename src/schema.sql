CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario    TEXT NOT NULL UNIQUE CHECK (length(trim(usuario)) > 0),
    clave_hash TEXT NOT NULL CHECK (length(clave_hash) > 0),
    rol        TEXT NOT NULL CHECK (rol IN ('operador', 'admin'))
);

CREATE TABLE IF NOT EXISTS lotes (
    codigo          TEXT NOT NULL PRIMARY KEY CHECK (length(trim(codigo)) > 0),
    productor       TEXT NOT NULL CHECK (length(trim(productor)) > 0),
    origen          TEXT NOT NULL CHECK (length(trim(origen)) > 0),
    fecha_recepcion TEXT NOT NULL CHECK (length(trim(fecha_recepcion)) > 0),  
    cantidad        REAL NOT NULL CHECK (cantidad > 0),
    unidad          TEXT NOT NULL DEFAULT 'kg' CHECK (length(trim(unidad)) > 0),
    creado_por      TEXT NOT NULL,                   
    creado_en       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS transformaciones (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    op_id            TEXT NOT NULL UNIQUE CHECK (length(trim(op_id)) > 0),  
    lote_codigo      TEXT NOT NULL REFERENCES lotes(codigo),
    etapa            TEXT NOT NULL CHECK (length(trim(etapa)) > 0),
    responsable      TEXT NOT NULL CHECK (length(trim(responsable)) > 0),
    fecha            TEXT NOT NULL CHECK (length(trim(fecha)) > 0),
    entrada          REAL NOT NULL CHECK (entrada > 0),
    salida           REAL NOT NULL CHECK (salida >= 0),
    costo_total      REAL NOT NULL DEFAULT 0 CHECK (costo_total >= 0),
    costos_incluidos TEXT,
    incidencias      TEXT,
    justificacion    TEXT,
    creado_por       TEXT NOT NULL,
    creado_en        TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (salida <= entrada OR length(trim(COALESCE(justificacion, ''))) > 0),
    CHECK (costo_total = 0 OR length(trim(COALESCE(costos_incluidos, ''))) > 0)
);

CREATE TABLE IF NOT EXISTS productos (
    codigo            TEXT NOT NULL PRIMARY KEY CHECK (length(trim(codigo)) > 0),  
    transformacion_id INTEGER NOT NULL REFERENCES transformaciones(id),
    lote_codigo       TEXT NOT NULL REFERENCES lotes(codigo),
    nombre            TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    cantidad          REAL NOT NULL CHECK (cantidad > 0),
    unidad            TEXT NOT NULL DEFAULT 'kg' CHECK (length(trim(unidad)) > 0),
    precio_venta      REAL NOT NULL CHECK (precio_venta >= 0),
    estado            TEXT NOT NULL DEFAULT 'pendiente'
                      CHECK (estado IN ('pendiente', 'liberado', 'bloqueado')),
    motivo_estado     TEXT,
    CHECK (estado = 'pendiente' OR length(trim(COALESCE(motivo_estado, ''))) > 0)
);

CREATE TABLE IF NOT EXISTS alertas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_codigo       TEXT NOT NULL REFERENCES lotes(codigo),
    transformacion_id INTEGER REFERENCES transformaciones(id),
    tipo              TEXT NOT NULL CHECK (length(trim(tipo)) > 0),    
    regla             TEXT NOT NULL CHECK (length(trim(regla)) > 0),   
    causa             TEXT NOT NULL CHECK (length(trim(causa)) > 0),   
    creada_en         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS pedidos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,             -- se muestra como PED-0001
    token           TEXT NOT NULL UNIQUE CHECK (length(token) >= 16), -- enlace privado del comprador
    producto_codigo TEXT NOT NULL REFERENCES productos(codigo),
    comprador       TEXT NOT NULL CHECK (length(trim(comprador)) > 0),
    direccion       TEXT NOT NULL CHECK (length(trim(direccion)) > 0),
    telefono        TEXT NOT NULL CHECK (length(trim(telefono)) > 0),
    correo          TEXT NOT NULL CHECK (correo LIKE '%_@_%._%'),
    kilos           REAL NOT NULL CHECK (kilos > 0),
    precio_kg       REAL NOT NULL CHECK (precio_kg >= 0),          -- precio congelado al pedir
    estado          TEXT NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'cancelado')),
    motivo_estado   TEXT,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    actualizado_en  TEXT,
    CHECK (estado = 'pendiente' OR length(trim(COALESCE(motivo_estado, ''))) > 0)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario        TEXT NOT NULL CHECK (length(trim(usuario)) > 0),   
    fecha          TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    accion         TEXT NOT NULL CHECK (length(trim(accion)) > 0),
    entidad        TEXT NOT NULL CHECK (length(trim(entidad)) > 0),
    entidad_id     TEXT,                                              
    campo          TEXT,
    valor_anterior TEXT,
    valor_nuevo    TEXT
);


CREATE INDEX IF NOT EXISTS idx_lotes_origen            ON lotes(origen);
CREATE INDEX IF NOT EXISTS idx_transformaciones_lote   ON transformaciones(lote_codigo);
CREATE INDEX IF NOT EXISTS idx_productos_lote          ON productos(lote_codigo);
CREATE INDEX IF NOT EXISTS idx_productos_transf        ON productos(transformacion_id);
CREATE INDEX IF NOT EXISTS idx_productos_estado        ON productos(estado);
CREATE INDEX IF NOT EXISTS idx_alertas_lote            ON alertas(lote_codigo);
CREATE INDEX IF NOT EXISTS idx_pedidos_producto        ON pedidos(producto_codigo, estado);
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad       ON auditoria(entidad, entidad_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha         ON auditoria(fecha);

CREATE VIEW IF NOT EXISTS v_inventario_lote AS
SELECT
    codigo, productor, origen, fecha_recepcion, unidad,
    recibido,
    consumido,
    recibido - consumido AS disponible,
    costo_total,
    estados
FROM (
    SELECT
        l.codigo, l.productor, l.origen, l.fecha_recepcion, l.unidad,
        l.cantidad AS recibido,
        COALESCE((SELECT SUM(t.entrada) FROM transformaciones t
                  WHERE t.lote_codigo = l.codigo), 0) AS consumido,
        COALESCE((SELECT SUM(t.costo_total) FROM transformaciones t
                  WHERE t.lote_codigo = l.codigo), 0) AS costo_total,
        COALESCE((SELECT GROUP_CONCAT(DISTINCT p.estado) FROM productos p
                  WHERE p.lote_codigo = l.codigo), 'sin producto') AS estados
    FROM lotes l
);

CREATE VIEW IF NOT EXISTS v_ficha_publica AS
SELECT
    p.codigo      AS codigo_producto,
    p.nombre,
    p.cantidad,
    p.unidad,
    p.precio_venta,
    p.estado,
    CASE WHEN p.estado = 'liberado' THEN 1 ELSE 0 END AS en_venta,
    l.codigo      AS lote_codigo,
    l.origen,
    l.fecha_recepcion,
    t.etapa,
    t.fecha       AS fecha_transformacion
FROM productos p
JOIN lotes l            ON l.codigo = p.lote_codigo
JOIN transformaciones t ON t.id     = p.transformacion_id;

-- Kilos de cada producto que aún se pueden pedir: lo producido menos lo apartado por pedidos activos
CREATE VIEW IF NOT EXISTS v_producto_disponible AS
SELECT
    p.codigo,
    p.cantidad,
    COALESCE((SELECT SUM(d.kilos) FROM pedidos d
              WHERE d.producto_codigo = p.codigo AND d.estado IN ('pendiente', 'aprobado')), 0) AS apartado,
    p.cantidad - COALESCE((SELECT SUM(d.kilos) FROM pedidos d
              WHERE d.producto_codigo = p.codigo AND d.estado IN ('pendiente', 'aprobado')), 0) AS disponible
FROM productos p;

CREATE TRIGGER IF NOT EXISTS trg_pedidos_solo_liberados
BEFORE INSERT ON pedidos
WHEN (SELECT estado FROM productos WHERE codigo = NEW.producto_codigo) IS NOT 'liberado'
BEGIN
    SELECT RAISE(ABORT, 'PRODUCTO_NO_DISPONIBLE');
END;

CREATE TRIGGER IF NOT EXISTS trg_pedidos_sin_sobreventa
BEFORE INSERT ON pedidos
WHEN NEW.kilos > (SELECT disponible FROM v_producto_disponible WHERE codigo = NEW.producto_codigo) + 0.000001
BEGIN
    SELECT RAISE(ABORT, 'INVENTARIO_INSUFICIENTE');
END;

-- Rechazado y cancelado son finales: no se reabren ni cambian de producto o cantidad
CREATE TRIGGER IF NOT EXISTS trg_pedidos_estado_final
BEFORE UPDATE ON pedidos
WHEN OLD.estado IN ('rechazado', 'cancelado')
  OR NEW.kilos IS NOT OLD.kilos OR NEW.producto_codigo IS NOT OLD.producto_codigo OR NEW.precio_kg IS NOT OLD.precio_kg
BEGIN
    SELECT RAISE(ABORT, 'PEDIDO_CERRADO');
END;

CREATE TRIGGER IF NOT EXISTS trg_pedidos_no_borrar
BEFORE DELETE ON pedidos
BEGIN SELECT RAISE(ABORT, 'HISTORIAL_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_transformaciones_sin_sobreconsumo
BEFORE INSERT ON transformaciones
WHEN NOT EXISTS (SELECT 1 FROM transformaciones WHERE op_id = NEW.op_id)
 AND NEW.entrada > (
        (SELECT cantidad FROM lotes WHERE codigo = NEW.lote_codigo)
      - COALESCE((SELECT SUM(entrada) FROM transformaciones
                  WHERE lote_codigo = NEW.lote_codigo), 0)
     ) + 0.000001
BEGIN
    SELECT RAISE(ABORT, 'INVENTARIO_INSUFICIENTE');
END;

CREATE TRIGGER IF NOT EXISTS trg_transformaciones_inmutables
BEFORE UPDATE OF entrada, lote_codigo ON transformaciones
BEGIN
    SELECT RAISE(ABORT, 'TRANSFORMACION_INMUTABLE');
END;

CREATE TRIGGER IF NOT EXISTS trg_lotes_cantidad_minima
BEFORE UPDATE OF cantidad ON lotes
WHEN NEW.cantidad + 0.000001 < COALESCE(
        (SELECT SUM(entrada) FROM transformaciones WHERE lote_codigo = OLD.codigo), 0)
BEGIN
    SELECT RAISE(ABORT, 'LOTE_MENOR_QUE_CONSUMO');
END;

CREATE TRIGGER IF NOT EXISTS trg_lotes_no_borrar
BEFORE DELETE ON lotes
BEGIN SELECT RAISE(ABORT, 'HISTORIAL_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_transformaciones_no_borrar
BEFORE DELETE ON transformaciones
BEGIN SELECT RAISE(ABORT, 'HISTORIAL_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_productos_no_borrar
BEFORE DELETE ON productos
BEGIN SELECT RAISE(ABORT, 'HISTORIAL_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_alertas_no_borrar
BEFORE DELETE ON alertas
BEGIN SELECT RAISE(ABORT, 'HISTORIAL_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_auditoria_no_editar
BEFORE UPDATE ON auditoria
BEGIN SELECT RAISE(ABORT, 'AUDITORIA_INMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_auditoria_no_borrar
BEFORE DELETE ON auditoria
BEGIN SELECT RAISE(ABORT, 'AUDITORIA_INMUTABLE'); END;
