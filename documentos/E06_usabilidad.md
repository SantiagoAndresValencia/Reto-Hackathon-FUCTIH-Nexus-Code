# E06 · Verificación de experiencia de usuario

## 1. Prueba con una persona ajena al equipo

**Fecha:** 16/10/2026, ~6:20 a. m. · **Perfil general:** Ángel, estudiante de la Universidad
Surcolombiana, **participante del evento en otro equipo (TOBARU WORK TEAM)**, que no participó en el
desarrollo de Kaoka. Se declara que **no** es productor ni miembro de una asociación real. Se le dio
el usuario `operador` y solo se le leyó cada tarea, sin indicarle los clics.

| Tarea | Instrucción que se le dio | Tiempo | ¿Lo logró sin ayuda? | Dificultades observadas |
| --- | --- | --- | --- | --- |
| T1 · Iniciar sesión y registrar un lote | «Llegaron 60 kg de cacao seco del Productor E, de Pitalito, hoy. Regístrelo con el código CAC010.» | 2 min | Sí | Ninguna observada |
| T2 · Encontrar su trazabilidad | «Ahora encuentre cuánto llegó de ese lote y cuánto queda disponible.» | 1 min | Sí | Ninguna observada |

**Total:** 3 minutos para las dos tareas, sin pedir ayuda y sin cometer errores.

**Comentario de la persona:** no hizo comentarios ni sugerencias.

## 2. Mejora derivada de la prueba

En esta prueba **no se observaron dificultades** y la persona no sugirió cambios, así que no hubo
una dificultad de la cual derivar una mejora. Lo declaramos como limitación: una sola persona,
estudiante con experiencia en tecnología, no representa a un operador de planta. La prueba se
repetirá en la semana 1 del piloto (E09) con un operador real de la asociación, en celular, y de ahí
saldrán las mejoras.

## 3. Verificaciones de accesibilidad hechas por el equipo

Ejecutadas automáticamente en Chromium el 16/10/2026 sobre la versión de entrega (commit `ca3d77c` más la corrección de `ficha.html`).

| Verificación | Método | Resultado | Evidencia |
| --- | --- | --- | --- |
| Vista móvil | Pantallas Lotes, Transformar, Ficha y Vista del comprador a 390×844 | Sin desplazamiento horizontal (ancho de página 390 px); el menú lateral se convierte en un botón de menú (☰) y la tabla de lotes en tarjetas | `evidencias/movil_lotes.png`, `movil_transformar.png`, `movil_comprador.png`, `cp13_ficha_bloqueada_movil.png` |
| Etiquetas de formularios | Script que busca campos visibles sin `<label>` ni `aria-label` en Transformar | Ningún campo sin etiqueta | CP19 en E05 |
| Navegación por teclado | Iniciar sesión solo con Tab y Enter; recorrer Recibir lote con Tab | El foco empieza en «Usuario»; Tab pasa a «Clave»; Enter entra. En Recibir lote el orden es: *Saltar al contenido* → menú (incluye Vista del comprador y Pedidos) → código → productor → origen → fecha | `evidencias/teclado.txt` |
| Foco visible | Estilo calculado del campo con foco | Anillo de foco verde de 4 px (`box-shadow`) | `evidencias/teclado_foco.png` |
| Mensajes de error comprensibles | Casos negativos de E05 | Dicen qué campo corregir y conservan lo escrito: «El campo «Cantidad» debe ser mayor que 0», «Ya existe un lote con el código CAC001», «No hay suficiente cacao disponible en CAC002» | CP04–CP06, CP09 |
| Contraste | Revisión visual de las capturas (no se midió con herramienta) | Texto oscuro sobre paneles claros; estados con color **y** texto (no solo color) | Capturas de E05 |
| Movimiento reducido | CSS con `prefers-reduced-motion` | Las animaciones se desactivan si el usuario lo pide en su sistema | `src/static/kaoka.css` |
