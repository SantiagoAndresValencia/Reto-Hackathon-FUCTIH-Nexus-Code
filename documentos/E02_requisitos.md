# E02 · Requisitos y organización del equipo

**Equipo Nexus Code:** Santiago Valencia (backend: validaciones, lotes, permisos, productos, respaldo,
integración y pruebas de flujo) · Thomas Chica (base de datos: `schema.sql`, restricciones, triggers,
vistas y sus pruebas) · David Rojas Ipuz (cálculos de merma, costo y margen; diseño visual Kaoka).
Trabajo en ramas `feature/*` unidas a `main` mediante Pull Requests (#1 a #19).

## Historias de usuario

| ID | Req. | Como… quiero… para… | Prior. | Criterio de aceptación (Dado / cuando / entonces) | Resp. | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| HU01 | RF01 | Como **operador** quiero registrar un lote con productor, origen, fecha, cantidad y unidad para saber qué cacao entró y de dónde | Alta | Dado el formulario, cuando registro CAC004, Neiva, 50 kg, entonces queda guardado con código único y persiste | Santiago | Hecho |
| HU02 | RF01 | Como **operador** quiero que se rechacen cantidades no positivas y campos vacíos para no guardar datos falsos | Alta | Dado cantidad −5 o productor vacío, cuando guardo, entonces veo un mensaje claro, no se guarda nada y conservo lo escrito | Santiago / Thomas | Hecho |
| HU03 | RF01 | Como **operador** quiero que el código del lote no se repita para no confundir lotes | Alta | Dado CAC001 existente, cuando registro otro CAC001, entonces se rechaza con «Ya existe un lote con el código CAC001» | Santiago / Thomas | Hecho |
| HU04 | RF02 | Como **operador** quiero registrar una etapa con responsable, fecha, entrada, salida e incidencias para vincular el producto con su lote | Alta | Dado CAC001 con 100 kg, cuando registro Secado 100 → 80 kg, entonces se crea P-CAC001-1 ligado a CAC001 | Santiago | Hecho |
| HU05 | RF08 | Como **operador** quiero registrar una transformación para conocer la existencia restante sin poder consumir de más | Alta | Dado un lote con 100 kg disponibles, cuando solicito consumir 120 kg, entonces se rechaza y siguen 100 kg | Thomas / Santiago | Hecho |
| HU06 | RF08 | Como **operador** quiero que reenviar el formulario no descuente dos veces para evitar errores por doble clic o F5 | Alta | Dada una operación enviada dos veces con el mismo identificador, entonces solo se consume una vez y se avisa «ya estaba registrada» | Thomas / Santiago | Hecho |
| HU07 | RF03 | Como **administrador** quiero ver el recorrido de un lote hasta el producto para reconstruir el origen | Alta | Dado CAC001 transformado, cuando abro su detalle, entonces veo recepción, etapas, productos, alertas y cantidades | Santiago | Hecho |
| HU08 | RF04 | Como **administrador** quiero una alerta cuando la merma supere 15 % o el costo no sea calculable para decidir a tiempo | Alta | Dado 100 → 80 kg, entonces aparece «Merma mayor a 15 %» con la causa «Merma de 20 %»; dada salida 0, alerta de costo | Dabidri / Santiago | Hecho |
| HU09 | RF05, RF12 | Como **administrador** quiero ver costo unitario y margen con fórmula, unidades y costos incluidos para fijar el precio | Alta | Dado 1.600.000 COP, 80 kg y precio 25.000, entonces veo 20.000 COP/kg y 20 %; con salida 0 dice «No calculable» sin error | Dabidri | Hecho |
| HU10 | RF09 | Como **administrador** quiero liberar o bloquear un producto con motivo para controlar qué se vende | Alta | Dado un operador, cuando intenta liberar (aun enviando la petición directa), entonces recibe «Acción denegada» (403), el estado no cambia y el intento queda auditado | Santiago | Hecho |
| HU11 | RF06 | Como **comprador** quiero consultar la ficha de un producto por enlace o código para confiar en su origen | Alta | Dado P-CAC001-1, cuando lo consulto sin sesión, entonces veo origen, fechas, etapa y estado, pero no costos, precio ni productor | Santiago / Dabidri | Hecho |
| HU12 | RF07 | Como **administrador** quiero que los datos sigan al reiniciar y poder restaurar un respaldo para no perder registros | Alta | Dado un respaldo, cuando restauro, entonces lotes, kg, transformaciones, productos y auditoría coinciden («INTEGRIDAD OK») | Santiago | Hecho |
| HU13 | RF10 | Como **administrador** quiero ver quién cambió qué y cuándo, con valor anterior y nuevo, para evitar cambios ocultos | Media | Dado un bloqueo, la auditoría muestra usuario, fecha y «pendiente → bloqueado»; ningún registro se puede borrar ni editar | Santiago / Thomas | Hecho |
| HU14 | RF11 | Como **administrador** quiero filtrar lotes por origen o estado y exportar CSV para reportar a compradores | Media | Dado el filtro Rivera, cuando exporto, entonces el CSV trae solo CAC001 con cantidades, estado y costos; el operador no puede exportar | Santiago | Hecho |
| HU15 | Hora 12 | Como **administrador** quiero bloquear el producto de CAC001 ante un reclamo, ver su origen y las cantidades afectadas para responder al comprador | Alta | Ver tarjeta de cambio TC-01 (criterio ajustado) | Santiago | Hecho |
| HU16 | Diferenc. | Como **administrador** quiero un precio sugerido según el margen objetivo para no vender a pérdida | Media | Dado un costo de 20.000 COP/kg y margen objetivo 30 %, entonces el detalle sugiere 28.571 COP/kg; sin costo muestra «—» | Santiago | Hecho |

## Requisitos de calidad

| Calidad | Cómo se cumple | Verificación |
| --- | --- | --- |
| Permisos en la capa de datos | `@solo_admin` y `exigir_admin()` en el servidor; 403 aunque se salte la interfaz | CP12, `test_operador_no_puede_liberar` |
| Integridad sin registros parciales | Transacciones `with db:`; CHECK y triggers en SQLite | CP04, CP09, `test_schema.py` |
| Historial inmutable | Triggers que impiden DELETE en lotes, transformaciones, productos y alertas, y UPDATE/DELETE en auditoría | `test_historial_no_se_borra`, `test_auditoria_es_solo_de_agregar` |
| Privacidad del comprador | La ficha lee solo campos autorizados de la vista `v_ficha_publica` | CP13, `test_ficha_publica_sin_costos_ni_productor` |
| Rendimiento | Trazabilidad de 100 registros ≤ 3 s | `scripts/medir_rendimiento.py`: 0,067 s máx. |
| Móvil y accesibilidad | Diseño adaptable, etiquetas en todos los campos, navegación con teclado | CP19, E06 |
| Seguridad de sesión | Clave secreta fuera del código, cookie HttpOnly y SameSite=Lax | `test_cookie_falsificada_con_clave_antigua_no_entra` |

## Tablero de tareas (exportación)

Columnas: Por hacer → En progreso → Revisión (PR) → Hecho. Estado al cierre:

| Tarea | Historia | Responsable | Commit / PR | Estado |
| --- | --- | --- | --- | --- |
| Base Flask y estructura del repo | — | Santiago | `4f18048` · PR #1 | Hecho |
| Esquema SQLite: tablas, CHECK, triggers, vistas | HU02–06, HU11, HU13 | Thomas | `0088a18` | Hecho |
| Validaciones de formularios | HU01–03 | Santiago | `017050a` · PR #2 | Hecho |
| Recepción de lotes (lógica y pantalla) | HU01–03 | Santiago | `09f89d6`, `1dd8da4`, `6af3c52` · PR #4, #5, #9 | Hecho |
| Cálculos de merma, costo y margen | HU08, HU09 | Dabidri | `f91a0d2` · PR #8 | Hecho |
| Transformación con op_id y alertas | HU04–06, HU08 | Santiago | `f3dd415`, `9b8fded`, `5fd725c` · PR #10, #11 | Hecho |
| Auditoría | HU13 | Santiago | `24e2fd0`, `23ff725` | Hecho |
| Login, roles y 403 | HU10 | Santiago | `a80fccf` · PR #12 | Hecho |
| Respaldo y restauración | HU12 | Santiago | `e8efe97` · PR #13 | Hecho |
| Trazabilidad, estados, ficha, CSV, datos demo | HU07, HU10, HU11, HU14 | Santiago | `ff9a02f` · PR #14 | Hecho |
| Pruebas de autenticación, productos y flujo | Todas | Santiago | `746db51` · PR #16 | Hecho |
| Diseño visual Kaoka y consulta pública por código | HU11, UX | Dabidri | `0abdc0d`, merge `c72d35f` | Hecho |
| Corrección de textos | UX | Thomas | `ed7d78e` | Hecho |
| Revisión de seguridad y precio justo sugerido | HU16, calidad | Santiago | `7b4bce1` · PR #19 | Hecho |
| Incidencia hora 12 (TC-01) y documentación | HU15 | Equipo | commit de documentación | Hecho |

Historial completo: `git log --oneline` y la pestaña *Pull requests* del repositorio.

## Tarjeta de cambio TC-01 · Incidencia de la hora 12

| Campo | Contenido |
| --- | --- |
| Origen | Anuncio común de la organización: el comprador informa un problema con CAC001 |
| Pedido | El administrador debe bloquear el producto, identificar su origen y explicar las cantidades afectadas, sin borrar historial |
| Análisis | El producto de CAC001 es P-CAC001-1. El bloqueo con motivo (RF09), la ficha pública y el historial inmutable ya existían. Las cantidades afectadas se leen en el detalle del lote |
| Criterio ajustado (HU15) | **Dado** el reclamo sobre CAC001, **cuando** el administrador bloquea P-CAC001-1 con el motivo «Reclamo del comprador sobre CAC001», **entonces** (1) la ficha pública muestra «Producto bloqueado: no disponible para la venta» con origen Rivera y lote CAC001; (2) el detalle del lote muestra origen (Productor A, Rivera, recibido el 2026-10-15) y cantidades: **100 kg recibidos, 100 kg transformados, 80 kg de producto bloqueado, 20 kg de merma, 0 kg disponibles**; (3) la auditoría registra admin, fecha y «pendiente → bloqueado»; (4) no se borra ningún registro |
| Cambio en código | Ninguno: el comportamiento ya cumplía el criterio ajustado |
| Validación | Regresión: suite completa (68 pruebas, todas pasan), incluida `test_bloquear_se_ve_en_ficha_y_auditoria`; casos manuales CP13 y CP14 en E05 |
| Limitación | Si un lote tuviera varios productos, se bloquean uno por uno. Bloqueo de lote completo en un clic: mejora 1 de E07 |

## Matriz de trazabilidad (requisito → componente → prueba → resultado → evidencia)

| Req. | Componente o pantalla | Prueba automatizada | Caso E05 | Resultado |
| --- | --- | --- | --- | --- |
| RF01 | `lotes.crear_lote`, `validaciones.py`, Recibir lote | `test_crea_lote_y_queda_disponible`, `test_lote_invalido_no_se_guarda`, `test_codigo_repetido`, `test_cantidad_debe_ser_positiva` | CP03–CP06 | Pasa |
| RF02 | `lotes.registrar_transformacion`, Transformar | `test_transformacion_crea_producto_y_alerta_de_merma` | CP07 | Pasa |
| RF03 | `lotes.trazabilidad`, Detalle del lote | `test_flujo_completo_del_jurado` | CP11 | Pasa |
| RF04 | `calculos.alertas_de`, tabla `alertas` | `test_transformacion_crea_producto_y_alerta_de_merma` | CP07, CP10 | Pasa |
| RF05 | `calculos.costo_unitario`, `margen`, indicadores | `test_costo_unitario_ejemplo_del_reto`, `test_margen_ejemplo_del_reto` | CP11 | Pasa |
| RF06 | `productos.ficha_publica`, `/consultar`, `/ficha/<código>` | `test_ficha_publica_sin_costos_ni_productor`, `test_ficha_publica_no_expone_datos_internos` | CP13 | Pasa |
| RF07 | `db.py`, `respaldo.py` | `test_respaldo_y_restauracion`, `test_restaurar_archivo_inexistente_no_toca_la_base` | CP16, CP17 | Pasa |
| RF08 | `v_inventario_lote`, trigger de sobreconsumo, `op_id` único | `test_no_consume_mas_de_lo_disponible`, `test_reenvio_no_consume_dos_veces` | CP08, CP09 | Pasa |
| RF09 | `productos.cambiar_estado`, `auth.exigir_admin` | `test_operador_no_puede_liberar`, `test_bloquear_sin_motivo_no_cambia` | CP12, CP13 | Pasa |
| RF10 | `auditoria.registrar`, Auditoría | `test_bloquear_se_ve_en_ficha_y_auditoria`, `test_auditoria_es_solo_de_agregar` | CP14 | Pasa |
| RF11 | `lotes.filtrar_lotes`, `productos.resumen_csv` | `test_csv_filtrado_por_origen`, `test_operador_no_exporta_csv` | CP15 | Pasa |
| RF12 | `calculos.*`, división entre cero controlada | `test_costo_unitario_salida_cero_no_divide`, `test_margen_precio_cero_no_divide` | CP10, CP11 | Pasa |
| Hora 12 | Estados, ficha, detalle, auditoría | `test_bloquear_se_ve_en_ficha_y_auditoria` + suite completa | CP13, CP14 | Pasa |
| Diferenc. | `calculos.precio_sugerido`, indicador «Precio justo sugerido» | `test_precio_sugerido` | CP11 | Pasa |

Evidencias en `documentos/evidencias/` (capturas `cpXX_*.png`, `pytest_salida.txt`).

## Funciones incompletas o parciales

- Bloqueo de un lote completo en un clic: no existe; se bloquea cada producto (suficiente para CAC001, que tiene uno).
- RF06 por QR: se cumple por enlace y por código; no se genera QR.
- RF04: se implementan alertas por merma y por costo; no por retraso ni por registro incompleto (los campos obligatorios se validan antes de guardar).
- Gestión de usuarios y cambio de contraseña desde la interfaz: no incluidos (usuarios de demostración por comando).
