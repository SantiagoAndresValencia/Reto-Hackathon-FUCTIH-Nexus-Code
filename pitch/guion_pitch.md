# Guion del pitch · 5 minutos

Antes de empezar: app abierta en `/login`, base recién restaurada
(`flask --app src/app restaurar datos/respaldo_demo.db`), celular con `/consultar` abierto.

| Tiempo | Quién | Qué se dice / se hace |
| --- | --- | --- |
| 0:00–0:40 | Diapositiva 1 | «Una asociación del Huila recibe cacao de varias fincas y lo anota en cuadernos. Cuando un comprador reclama, nadie sabe de qué lote salió, cuánto se perdió ni cuánto costó.» |
| 0:40–1:10 | Diapositiva 2 | «Kaoka le da historia a cada kilo: del lote al comprador, con merma, costo y precio justo calculados en el momento.» |
| 1:10–3:10 | **Demo en vivo** | 1) Entrar como `operador` → **Transformar CAC001**: Secado, 100 → 80 kg, costo 1.600.000, precio 25.000 → «Transformación registrada». 2) Intentar 50 kg más → «No hay suficiente cacao». 3) Salir, entrar como `admin` → CAC001: merma 20 % con alerta, 20.000 COP/kg, margen 20 %, **precio justo 28.571**. 4) **Bloquear** con motivo «Reclamo del comprador». 5) En el celular: `P-CAC001-1` → «Producto bloqueado», origen Rivera, sin costos. |
| 3:10–4:10 | Diapositiva 4 | «Paga la asociación: 130.000 COP al mes. Incluye instalación, capacitación, respaldo y soporte. Lo calculamos con nuestra propia fórmula: 90.000 de costo ÷ 0,7.» |
| 4:10–4:40 | Diapositiva 3 | «Nuestro diferenciador: no solo rastreamos el cacao, le decimos al productor a qué precio vender para no perder plata. Y funciona sin Internet.» |
| 4:40–5:00 | Diapositiva 5 | «Proponemos un piloto de 30 días. Mediremos trazabilidad, tiempo de respuesta a reclamos y mermas. Buscamos una asociación aliada.» |

## Preguntas probables del jurado

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Qué pasa si el operador intenta liberar saltándose la pantalla? | El servidor responde 403 y lo anota en la auditoría (`@solo_admin`, `exigir_admin`). Ocultar el botón es solo visual |
| ¿Cómo evitan el doble consumo? | Cada formulario lleva un `op_id` único; si llega dos veces, la base lo rechaza y avisamos «ya estaba registrada» |
| ¿Y si alguien borra un registro? | No se puede: triggers en SQLite impiden borrar lotes, transformaciones, productos y alertas, y editar la auditoría |
| ¿Cómo saben que el respaldo sirve? | `restaurar` compara lotes, kg, transformaciones, productos y auditoría, y dice INTEGRIDAD OK |
| ¿Por qué SQLite? | Cero instalación, sin Internet, respaldo de un archivo; límite: una escritura a la vez |
| ¿Usaron IA? | Sí, como asistente; está declarado en el README y E08 con qué archivos y cómo lo revisamos. El producto no usa IA |
