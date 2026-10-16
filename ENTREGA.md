# ENTREGA · Kaoka (E10)

| Campo | Valor |
| --- | --- |
| Equipo | Nexus Code |
| Integrantes | Santiago Andrés Valencia · Thomas Santiago Chica Perdomo · David Rojas Ipuz |
| Universidad | Universidad Surcolombiana sede Neiva |
| Reto | II Hackathon USCO · Agroindustria · «Cacao con historia, calidad y valor» |
| Repositorio | <https://github.com/SantiagoAndresValencia/Reto-Hackathon-FUCTIH-Nexus-Code> |
| Etiqueta final | `entrega-final` |
| Commit final (hash completo) | El de la etiqueta `entrega-final` (`git rev-parse entrega-final`); se registra también en el canal oficial (Devpost) |
| Diferenciador | Apoyo a la venta: precio justo sugerido + catálogo público y pedidos sin sobreventa |

## Acceso para el jurado

```bash
git clone https://github.com/SantiagoAndresValencia/Reto-Hackathon-FUCTIH-Nexus-Code.git prueba-jurado
cd prueba-jurado
git checkout entrega-final
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m flask --app src/app cargar-demo
.venv\Scripts\python.exe -m pytest -v
.venv\Scripts\python.exe -m flask --app src/app run
```

Usuarios: `operador / operador123` (operador) · `admin / admin123` (administrador).
Comprador: **Vista del comprador**, sin sesión: catálogo, ficha por código (`P-CAC001-1` después de transformar CAC001) y pedidos.
Si falla la conexión del evento, la app funciona igual: no usa Internet.
Recuperar los datos base: `flask --app src/app restaurar datos/respaldo_demo.db` 

## Lista de entregables

| ID | Entregable | Archivo |
| --- | --- | --- |
| E01 | Comprensión del problema y propuesta de valor | `documentos/E01_problema.pdf` (.md) |
| E02 | Requisitos, tablero, tarjeta de cambio de la hora 12 y matriz | `documentos/E02_requisitos.pdf` (.md) |
| E03 | Diseño: flujo, arquitectura, modelo de datos, decisiones | `documentos/E03_diseno.pdf` (.md), `documentos/diagramas/` |
| E04 | Producto y código fuente | `src/`, `requirements.txt`, datos demo (`cargar-demo`) |
| E05 | Informe de pruebas y pruebas automatizadas | `documentos/E05_pruebas.pdf` (.md), `src/tests/`, `documentos/evidencias/` |
| E06 | Verificación de experiencia de usuario | `documentos/E06_usabilidad.pdf` (.md) |
| E07 | Instalación, respaldo y mantenimiento | `README.md`, `documentos/E07_operacion.pdf` (.md), `datos/respaldo_demo.db` |
| E08 | Declaración de IA y componentes externos | `documentos/E08_IA_y_fuentes.md` (.pdf) |
| E09 | Pitch (5 diapositivas) y piloto | `pitch/E09_presentacion.pdf`, `documentos/E09_piloto.pdf` (.md) |
| E10 | Este índice y la matriz | `ENTREGA.md` |

## Matriz de trazabilidad (requisito → componente → prueba → resultado → evidencia)

| Req. | Componente o pantalla | Prueba automatizada | Caso | Resultado | Evidencia |
| --- | --- | --- | --- | --- | --- |
| RF01 Recepción | `lotes.crear_lote`, `validaciones.py` · Recibir lote | `test_crea_lote_y_queda_disponible`, `test_codigo_repetido`, `test_cantidad_debe_ser_positiva` | CP03–CP06 | Pasa | `cp03…cp06_*.png` |
| RF02 Transformación | `lotes.registrar_transformacion` · Transformar | `test_transformacion_crea_producto_y_alerta_de_merma` | CP07 | Pasa | `cp07_transformacion.png` |
| RF03 Trazabilidad | `lotes.trazabilidad` · Detalle del lote | `test_flujo_completo_del_jurado` | CP11 | Pasa | `cp11_trazabilidad_admin.png` |
| RF04 Alertas | `calculos.alertas_de`, tabla `alertas` | `test_transformacion_crea_producto_y_alerta_de_merma` | CP07, CP10 | Pasa | `cp10_salida_cero.png` |
| RF05 Indicador económico | `calculos.costo_unitario`, `margen` | `test_costo_unitario_ejemplo_del_reto`, `test_margen_ejemplo_del_reto` | CP11 | Pasa | `cp11_trazabilidad_admin.png` |
| RF06 Ficha comercial | `productos.ficha_publica` · `/consultar`, `/ficha/<código>` | `test_ficha_publica_sin_costos_ni_productor` | CP13 | Pasa | `cp13_ficha_bloqueada_movil.png` |
| RF07 Persistencia | `db.py`, `respaldo.py` | `test_respaldo_y_restauracion` | CP16, CP17 | Pasa | `cp16_tras_reiniciar.png`, `cp17_respaldo_restauracion.txt` |
| RF08 Inventario | `v_inventario_lote`, trigger, `op_id` | `test_no_consume_mas_de_lo_disponible`, `test_reenvio_no_consume_dos_veces` | CP08, CP09 | Pasa | `cp08_reenvio.txt`, `cp09_sin_existencia.png` |
| RF09 Estados | `productos.cambiar_estado`, `auth.exigir_admin` | `test_operador_no_puede_liberar`, `test_bloquear_sin_motivo_no_cambia` | CP12, CP13 | Pasa | `cp12_operador_denegado.png` |
| RF10 Auditoría | `auditoria.registrar` · Auditoría | `test_bloquear_se_ve_en_ficha_y_auditoria`, `test_auditoria_es_solo_de_agregar` | CP14 | Pasa | `cp14_auditoria.png` |
| RF11 Consulta y CSV | `lotes.filtrar_lotes`, `productos.resumen_csv` | `test_csv_filtrado_por_origen`, `test_operador_no_exporta_csv` | CP15 | Pasa | `cp15_resumen_rivera.csv` |
| RF12 Balance económico | `calculos.*` (sin división entre cero) | `test_costo_unitario_salida_cero_no_divide`, `test_margen_precio_cero_no_divide` | CP10, CP11 | Pasa | `cp10_salida_cero.png` |
| Hora 12 (TC-01) | Estados, ficha, detalle, auditoría | `test_bloquear_se_ve_en_ficha_y_auditoria` + suite 80/80 | CP13, CP14, CP20 | Pasa | E02 (tarjeta), E05 (regresión) |
| Rendimiento | Trazabilidad de 100 registros | `scripts/medir_rendimiento.py` | — | 0,144 s ≤ 3 s | `rendimiento_100_registros.txt` |
| Diferenciador | `calculos.precio_sugerido` | `test_precio_sugerido` | CP11 | Pasa | `cp11_trazabilidad_admin.png` |
| Venta (catálogo y pedidos) | `productos.catalogo`, `pedidos.py`, `v_producto_disponible`, triggers de pedidos | `test_pedidos.py` (11), `test_pedidos_no_sobrevenden_ni_se_reabren` | CP20–CP25 | Pasa | `cp20_catalogo.png` … `cp25_seguir_pedido.png` |

Evidencias en `documentos/evidencias/`.

## Funciones parciales (declaradas)

- RF04: alertas por merma y por costo; no por retraso ni por registro incompleto.
- RF06: por enlace, por código y en el catálogo; sin QR.
- Hora 12: el bloqueo es por producto (CAC001 tiene uno); no hay bloqueo de lote completo en un clic.
- Pedidos: sin pago en línea; el administrador confirma cada pedido.
- E06: la prueba de uso no mostró dificultades, por lo que no se derivó una mejora (ver el documento).
