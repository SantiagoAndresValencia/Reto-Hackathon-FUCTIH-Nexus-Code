# E05 · Informe de pruebas

**Versión probada:** commit `bc95156` (main, 16/10/2026 02:57) · **Fecha de ejecución:** 16/10/2026, 03:05–03:10
· **Entorno:** instalación limpia en entorno virtual nuevo (`pip install -r requirements.txt`), Python 3.13,
Flask 3.1.3, navegador Chromium automatizado (Playwright) en escritorio 1280×900 y celular 390×844.

## Pruebas automatizadas

Comando: `python -m pytest -v` → **68 passed en 7,05 s**. Salida completa: `evidencias/pytest_salida.txt`.

| Archivo | Pruebas | Qué verifica (lógica relevante, no repetición del código) |
| --- | --- | --- |
| `test_lotes.py` | 18 | Validaciones (vacíos, ≤ 0, texto, NaN, coma decimal, fecha), lote duplicado, consumo mayor al disponible, reenvío sin doble consumo, salida 0 sin producto, salida > entrada exige justificación, restaurar archivo inexistente |
| `test_schema.py` | 25 | Restricciones de la base: CHECK, `op_id` único, trigger de inventario, vistas, ficha sin datos internos, historial y auditoría inmutables |
| `test_calculos.py` | 10 | Merma, costo unitario y margen del ejemplo y con otros valores; división entre cero; precio sugerido |
| `test_productos.py` | 8 | Operador no libera (403 + auditoría), bloqueo visible en ficha y auditoría, motivo obligatorio, ficha sin costos, CSV filtrado, operador no exporta, producto inexistente 404, CSV sin fórmulas |
| `test_auth.py` | 5 | Sin sesión redirige, clave incorrecta, login, operador no entra a auditoría, cookie falsificada rechazada |
| `test_flujo_jurado.py` | 2 | Recorrido completo del jurado con valores del caso; respaldo y restauración sin pérdida ni duplicados |

## Casos ejecutados

Ejecutados en el navegador sobre la aplicación en marcha, partiendo de `cargar-demo`. Resultado obtenido
copiado de la pantalla; evidencia en `documentos/evidencias/`.

| ID | Req. | Datos | Pasos | Esperado | Obtenido | Estado | Evidencia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CP01 | RF09/Seguridad | Sin sesión | Abrir /lotes sin iniciar sesión | Redirige al login | Redirigió a /login | Pasa | `cp01_sin_sesion.png` |
| CP02 | Seguridad | operador / clave incorrecta | Iniciar sesión | Mensaje de error, no entra | Muestra «Usuario o contraseña incorrectos.» | Pasa | `cp02_login_fallido.png` |
| CP03 | RF01 | CAC004, Productor D, Neiva, 2026-10-15, 50 kg | Recibir lote → Registrar | Lote guardado con código único | «Lote CAC004 guardado.» | Pasa | `cp03_lote_valido.png` |
| CP04 | RF01 | Cantidad -5 kg | Recibir lote → Registrar | Mensaje claro, no guarda, conserva lo escrito | «El campo «Cantidad» debe ser mayor que 0»; productor conservado: sí | Pasa | `cp04_cantidad_negativa.png` |
| CP05 | RF01 | Productor vacío | Recibir lote → Registrar | Mensaje de campo obligatorio, no guarda | «El campo «Productor» es obligatorio.» | Pasa | `cp05_campo_vacio.png` |
| CP06 | RF01 | Código CAC001 ya existente | Recibir lote → Registrar | Rechaza el duplicado | «Ya existe un lote con el código CAC001.» | Pasa | `cp06_duplicado.png` |
| CP07 | RF02/RF04/RF08 | CAC001: entrada 100 kg, salida 80 kg | Transformar → Registrar | Registra, crea P-CAC001-1, merma 20 % y alerta > 15 % | «Transformación registrada.»; disponible 0 kg | Pasa | `cp07_transformacion.png` |
| CP08 | RF08 | Mismo op_id reenviado | Reenviar el mismo formulario | Un solo consumo | «Esta operación ya estaba registrada: no se consumió de nuevo.» | Pasa | `cp08_reenvio.txt` |
| CP09 | RF08 | CAC002 (150 kg): entrada 200 kg | Transformar → Registrar | Rechaza, el disponible sigue en 150 kg | «No hay suficiente cacao disponible en CAC002.»; disponible sigue en 150 kg | Pasa | `cp09_sin_existencia.png` |
| CP10 | RF05/RF12 | CAC003: entrada 10 kg, salida 0 kg, costo 50.000 | Transformar → ver detalle | Sin error; costo «No calculable»; alerta de costo | Registrada; detalle muestra «No calculable» y alerta «Salida vendible igual a 0» | Pasa | `cp10_salida_cero.png` |
| CP11 | RF03/RF04/RF05/RF12 | CAC001 tras 100→80 kg, 1.600.000 COP, 25.000 COP/kg | Detalle del lote como admin | Recorrido, merma 20 %, alerta, 20.000 COP/kg, margen 20 %, fórmulas; precio sugerido 28.571 | Muestra merma 20.0 %, 20.000 COP/kg, margen 20.0 %, fórmulas y precio sugerido 28.571 COP/kg | Pasa | `cp11_trazabilidad_admin.png` |
| CP12 | RF09 | Usuario operador; POST directo al servidor saltando la interfaz | Enviar «liberar P-CAC001-1» como operador | Acción denegada (403); estado sin cambio | El operador no ve los botones; el servidor responde 403 «Acción denegada» | Pasa | `cp12_operador_denegado.png` |
| CP13 | RF06/RF09/Hora 12 | Bloquear P-CAC001-1 como admin; consultar sin sesión en celular | Bloquear con motivo → Consultar producto | Ficha: bloqueado, origen Rivera, sin costos ni productor | Ficha pública muestra estado bloqueado y origen Rivera; no muestra costos, precio ni productor | Pasa | `cp13_ficha_bloqueada_movil.png` |
| CP14 | RF10 | Filtro CAC001 | Auditoría → Filtrar | Usuario, fecha, pendiente → bloqueado y el intento denegado | Lista admin «pendiente → bloqueado» con fecha y el intento DENEGADO del operador | Pasa | `cp14_auditoria.png` |
| CP15 | RF11 | Filtro origen = Rivera | Exportar CSV como admin | Solo CAC001 con cantidades, estado y costos | CSV con 1 fila: CAC001,Rivera,100.0,100.0,0.0,bloqueado,1600000.0 | Pasa | `cp15_resumen_rivera.csv` |
| CP16 | RF07 | Datos de los casos anteriores | Detener la app y volver a ejecutarla | Los datos siguen | Tras reiniciar se ven CAC001–CAC004 y sus estados | Pasa | `cp16_tras_reiniciar.png` |
| CP17 | RF07 | Base con los casos anteriores | flask respaldar y luego restaurar | Conteos e identificadores iguales | «INTEGRIDAD OK» | Pasa | `cp17_respaldo_restauracion.txt` |
| CP18 | Errores | URL inexistente | Abrir /no-existe | Página de error clara | «La página o el registro no existe.» | Pasa | `cp18_404.png` |
| CP19 | Usabilidad | Pantalla 390×844 (celular) | Lotes y Transformar en celular | Sin desplazamiento horizontal; todos los campos con etiqueta | Ancho de página 390px; campos sin etiqueta: ninguno | Pasa | `movil_transformar.png` |

**Resumen:** 19 de 19 casos pasan. Cobertura exigida por el reto: flujo feliz (CP03, CP07, CP11),
dato inválido (CP04, CP05), lote duplicado (CP06), falta de existencia (CP09), reenvío (CP08), costos
con salida cero (CP10), permiso denegado (CP12), bloqueo y consulta pública (CP13), cambio auditado
(CP14), persistencia (CP16), exportación (CP15), respaldo y restauración (CP17).

**Valores distintos a los del caso:** CAC004 de 50 kg (CP03), 200 kg sobre 150 kg (CP09), salida 0 kg
con costo 50.000 (CP10) y 100 transformaciones sintéticas (medición). Los resultados se calculan; no
son cifras fijas.

## Prueba de regresión del cambio de la hora 12 (TC-01)

| Paso | Resultado |
| --- | --- |
| Criterio ajustado de HU15 (E02) | Bloquear P-CAC001-1, ver origen y cantidades afectadas, historial conservado |
| Regresión automatizada | Suite completa tras el cambio: **68/68 pasan**, incluida `test_productos.py::test_bloquear_se_ve_en_ficha_y_auditoria` (bloquea P-CAC001-1 como admin y comprueba ficha «bloqueado» y auditoría «pendiente → bloqueado») |
| Regresión manual | CP13: ficha «Producto bloqueado: no disponible para la venta», origen Rivera, lote CAC001, 80 kg. CP14: auditoría con admin, fecha y «pendiente → bloqueado». CP11: detalle con 100 kg recibidos, 100 kg consumidos, 0 kg disponibles, merma 20 % (20 kg) |
| Historial | Ningún registro borrado: los triggers lo impiden (`test_historial_no_se_borra`) |

## Medición de rendimiento: trazabilidad con 100 registros

| Elemento | Valor |
| --- | --- |
| Método | `python scripts/medir_rendimiento.py`: base temporal; lote CAC100 con **100 transformaciones, 100 productos y 100 alertas**; se mide `GET /lotes/CAC100` (trazabilidad completa como admin) 20 veces después de cargar la aplicación |
| Equipo | Contenedor Linux x86_64, Intel Xeon 2,10 GHz, 2 núcleos, 7,8 GB RAM, Python 3.13.16 |
| Resultado | Primera consulta **0,067 s** · mediana **0,030 s** · máxima **0,067 s** → **cumple (≤ 3 s)** |
| Evidencia | `evidencias/rendimiento_100_registros.txt` |

Para la demostración en el equipo del stand, ejecutar el mismo comando y anotar aquí el resultado:
equipo: ____________________ · máxima: ______ s.

## Fallos encontrados durante el desarrollo y su corrección

| Fallo | Corrección |
| --- | --- |
| `ModuleNotFoundError: No module named 'src'` al ejecutar | Se agregó `src/__init__.py` (`cb8d154`) y se documentó ejecutar desde la raíz |
| Error 500 al transformar: columnas `antes/despues` no existían en `auditoria` | `auditoria.py` usa `valor_anterior/valor_nuevo` (`23ff725`) |
| Tabla de lotes rota (columna Disponible) | Plantilla corregida (`27cb66d`) |
| No se podía iniciar sesión: tabla `usuarios` vacía | Comando `cargar-demo` y usuarios documentados en README |
| La página de error mostraba el mensaje en verde | Variable separada `mensaje_error` |
| Clave de sesión fija en el código permitía falsificar una sesión de admin | Clave desde `CACAO_SECRET` o aleatoria; cookie HttpOnly y SameSite; prueba de regresión (`7b4bce1`) |
| Cambio de estado tomaba el lote desde el formulario | Se lee de la base; producto inexistente → 404 (`7b4bce1`) |
| CSV podía ejecutar fórmulas en Excel | Celdas que empiezan por `= + - @` se exportan como texto (`7b4bce1`) |
| `restaurar` con archivo inexistente o inválido | Se valida antes de tocar la base (`7b4bce1`) |

**Limitaciones pendientes:** bloqueo de lote completo en un clic; alertas por retraso o registro
incompleto; QR de la ficha. Ver E07 (mejoras de 30 días).
