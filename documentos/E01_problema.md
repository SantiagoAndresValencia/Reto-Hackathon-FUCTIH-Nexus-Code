# E01 · Comprensión del problema y propuesta de valor

**Equipo:** Nexus Code · **Producto:** Kaoka · **Reto:** Cacao con historia, calidad y valor

[Caso] = tomado del reto. [Supuesto] = decisión del equipo no verificada en campo. No se hicieron entrevistas ni consultas reales.

## La asociación y sus usuarios

**[Caso]** Asociación ficticia del Huila que recibe cacao seco de fincas de Rivera, Campoalegre y Algeciras y lo transforma.

| Usuario | Qué necesita |
| --- | --- |
| Operador de planta | Registrar recepción, transformación e incidencias |
| Administrador | Consultar cantidades, trazabilidad, costos y alertas; decidir qué se vende |
| Comprador | Consultar el origen y el estado del producto, sin ver datos internos |

## Cómo registra hoy y cuál es la dificultad prioritaria

**[Caso]** Los registros están dispersos en cuadernos, hojas de cálculo y mensajes.

**Dificultad prioritaria:** ante una pregunta o reclamo de un comprador, la asociación **no puede
reconstruir rápido de qué lote salió el producto, cuánto se perdió ni cuánto costó**.

**Consecuencias [Caso]:**
1. No se puede reconstruir el origen del producto ni responder a un reclamo con evidencia.
2. Las pérdidas (merma) no se detectan a tiempo.
3. No se conoce el costo unitario: se puede vender por debajo del costo sin saberlo.

## Objetivo del MVP

Conectar en un solo flujo **recepción → transformación → decisión → venta**, de modo que cada producto
tenga un código que lleva a su lote de origen, sus cantidades, su merma, su costo y su estado, y que el
comprador pueda consultarlo sin ver información privada.

**Propuesta de valor:** *"Cada kilo con historia: del lote al comprador, con merma, costo y precio justo
calculados en el momento."*

## Alcance

**Incluye:** RF01–RF12: recepción de lotes, transformaciones con control de existencia y doble envío,
trazabilidad, alertas de merma y costo, costo unitario y margen con fórmulas, estados pendiente /
liberado / bloqueado (solo admin, con motivo), ficha pública por enlace o código, auditoría inmutable,
filtros y CSV, respaldo y restauración verificada. Diferenciador: precio justo sugerido.

**Exclusiones:** pagos reales, sensores, IA en el producto, mezcla de lotes en una operación, gestión
de usuarios desde la interfaz, facturación e integraciones externas.

## Restricciones

1. **Conectividad limitada [Supuesto]:** la planta puede no tener Internet estable. Por eso Kaoka corre
   localmente en un computador, sin servicios externos, con SQLite en un solo archivo.
2. **Usuarios con poca formación técnica [Supuesto]:** lenguaje claro, mensajes de error que dicen qué
   corregir y pantallas que funcionan en celular.

## Indicadores de beneficio y cómo se miden

| Indicador | Cómo se mide | Línea base | Meta del piloto |
| --- | --- | --- | --- |
| **Completitud de trazabilidad:** % de productos cuya ficha muestra origen, transformación y estado | Productos con ficha completa ÷ productos registrados × 100 (consulta a la vista `v_ficha_publica`) | Con cuadernos: no medible [Supuesto] · En la demo: 100 % (CP13) | ≥ 95 % de los productos del mes |
| **Tiempo de respuesta a un reclamo:** minutos para identificar origen y kg afectados de un producto | Cronometrar desde que llega el código hasta tener lote, origen y kg en pantalla | Se mide el día 1 del piloto con el método actual | < 5 minutos |
| **Mermas detectadas:** % de transformaciones con merma calculada y alerta si supera 15 % | Transformaciones con merma ÷ transformaciones registradas | 0 % calculadas automáticamente [Supuesto] | 100 % |


**Reglas [Caso]:** merma, costo unitario y margen según el reto (CAC001: 20 %, 20.000 COP/kg, 20 %);
no son estándares agronómicos. No afirmamos reducir pérdidas reales sin medición de campo. **[Supuesto]** margen objetivo del precio sugerido: 30 %, ajustable en el piloto.
