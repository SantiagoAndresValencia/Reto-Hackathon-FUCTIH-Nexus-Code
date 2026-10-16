# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Operador** (trabajador de planta de una asociación cacaotera del Huila): recibe lotes de cacao seco de las fincas y registra cada etapa de transformación (secado, tostión…), a menudo desde el celular en la planta.
- **Administrador** de la asociación: revisa costos, mermas y márgenes; libera o bloquea productos con motivo; consulta la auditoría y exporta CSV.
- **Comprador** (público, sin sesión): consulta la ficha ("pasaporte") de un producto desde el celular para conocer su origen y si está disponible para la venta.
- **Jurado** del II Hackathon USCO 2026 (Reto Agroindustria): prueba el sistema en vivo durante 8 minutos y en un pitch de 2 minutos; una persona externa debe registrar un lote y encontrar su trazabilidad sin guía.

## Product Purpose
Convertir registros dispersos (cuadernos, hojas de cálculo, mensajes) en trazabilidad confiable: reconstruir el origen de cada producto, detectar pérdidas, calcular costos y dar información confiable al comprador. Éxito = el flujo recepción → transformación → alerta → ficha comercial se entiende y se demuestra sin explicación.

## Positioning
Cada producto se puede seguir hasta el lote, la finca simulada y el municipio del Huila de donde salió, con indicadores que siempre muestran su fórmula, sus unidades y sus supuestos, y con un historial que nunca se borra.

## Operating Context
- Aplicación Flask + Jinja con SQLite (`src/`), plantillas en `src/templates/`. Demo local, sin internet garantizado: sin CDN, todo servido desde el proyecto.
- Roles: operador, administrador (con sesión) y comprador (sin sesión). Los permisos se aplican en el servidor; ocultar botones es solo cosmético.
- Flujo de estados: lote recibido (sin producto, gris) → transformación(es) → producto pendiente (ámbar) → liberado (verde) | bloqueado (rojo) → ficha del comprador.
- Prueba del jurado: crear lote, cantidad negativa, 100→80 kg, costo y margen, ficha sin costos, sobreconsumo y reenvío (F5), bloquear CAC001, operador intentando liberar.

## Capabilities and Constraints
- Entidades: Lote (código, productor ficticio, municipio de origen, fecha, kg), Transformación (una etapa sobre un solo lote), Producto terminado (P-{lote}-{n}, estado y motivo), Alerta (tipo, regla, causa), Registro de auditoría inmutable.
- Indicadores: merma % = (entrada − salida) ÷ entrada × 100 (alerta > 15 %); costo unitario COP/kg = costo total ÷ salida vendible ("no calculable" si salida 0); margen % = (precio − costo unitario) ÷ precio × 100. Son reglas del ejercicio, no estándares agronómicos. Los valores nunca son fijos en pantalla.
- Reglas: no consumir más de lo disponible; reenviar un formulario no consume dos veces; salida > entrada solo con justificación; errores claros sin perder lo escrito; nada se borra; un solo lote por transformación.
- Ficha pública: sin costos, productor, responsable ni incidencias.
- Pendientes de backend: consulta pública por código, QR, "bloquear todo el lote", diferenciador (analítica de mermas, QR o accesibilidad), inicio del admin con alertas recientes.

## Brand Commitments
- Nombre provisional: **Kaoka**.
- Leyenda visible obligatoria: "Datos de una asociación simulada para demostración"; los productores son ficticios.
- Sin logo, colores ni fuentes fijados por el equipo.

## Evidence on Hand
Datos demo en `src/app.py` (CAC001 Rivera 100 kg, CAC002 Campoalegre 150 kg, CAC003 Algeciras 80 kg; usuarios operador/operador123 y admin/admin123). No hay asociación, compradores, testimonios ni cifras reales: no inventarlos.

## Product Principles
1. Todo dato se puede rastrear hasta su origen; nada se borra, se corrige con nuevos registros.
2. Cada indicador muestra fórmula, unidades y supuestos.
3. Una persona externa completa las tareas principales sin guía.
4. El servidor decide los permisos; la interfaz los explica.

## Accessibility & Inclusion
Desde 360 px de ancho; etiqueta en cada campo, contraste legible, navegación completa con teclado y mensajes de error comprensibles (puntúa en el criterio E06).
