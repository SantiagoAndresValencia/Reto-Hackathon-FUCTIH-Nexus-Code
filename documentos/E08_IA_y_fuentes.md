# E08 · Declaración de IA y componentes externos

**Sí usamos IA generativa** durante el evento, como asistente. El producto **no** usa IA en tiempo de
ejecución. Todo el trabajo se hizo entre el 15/10 (3:00 p. m.) y el 16/10 de 2026; no hay código previo
al evento.

## Bitácora de uso de IA

| Fecha y hora (aprox.) | Herramienta | Uso y aporte relevante | Componente o archivo | Revisión humana | Corrección hecha |
| --- | --- | --- | --- | --- | --- |
| 15/10, 3:00–4:30 p. m. | Claude (Anthropic), chat | Lectura del reto, plan por horas, reparto de roles, elección de Flask + SQLite y guía de Git | Plan de trabajo, `.gitignore` | Santiago: decidió la tecnología y el reparto con el equipo | Se ajustó el plan para 3 integrantes |
| 15/10, 4:00–11:00 p. m. | Claude (Anthropic), chat | Generó el código por partes y explicó cada una; Santiago lo ejecutó, lo probó y lo subió con commits propios | `db.py`, `validaciones.py`, `lotes.py`, `auditoria.py`, `auth.py`, `productos.py`, `respaldo.py`, `app.py`, plantillas HTML base, `conftest.py`, `test_lotes.py`, `test_auth.py`, `test_productos.py`, `test_flujo_jurado.py` | Santiago: revisó cada parte, la ejecutó, la probó en el navegador y subió cada commit | Errores encontrados al ejecutar y corregidos: falta de `src/__init__.py`, columnas de auditoría equivocadas (error 500), tabla de lotes rota, inicio de sesión sin usuarios (`cargar-demo`), mensaje de error en verde |
| 15/10, tarde | Claude (Anthropic), chat | Instrucciones (prompts) por rol para los compañeros | Base de datos y cálculos | Thomas y Dabidri | — |
| 15/10, tarde | Claude (Anthropic) | Thomas usó IA solo para generar las pruebas del esquema | `src/tests/test_schema.py` | Thomas: ejecutó las pruebas contra su `schema.sql` | |
| 15/10, tarde | Claude (Anthropic) | Dabidri usó IA como guía para diseñar los cálculos según las reglas del reto, y le pidió que generara sus pruebas | `src/calculos.py`, `src/tests/test_calculos.py` | Dabidri: comprobó los resultados con el ejemplo del reto (20 %, 20.000 COP/kg, 20 %) | |
| 15/10–16/10, noche | Claude (Anthropic) | Dabidri escribió los prompts con los que Claude generó el diseño visual Kaoka: plantillas, estilos, íconos y consulta pública por código. Santiago preparó con Claude el contexto (roles, rutas y variables de las plantillas) | `src/templates/*`, `src/static/kaoka.css`, `kaoka.js`, `_iconos.html`, ruta `/consultar` | Dabidri y Santiago: probaron que las rutas y los datos siguieran iguales; las 63 pruebas pasaban tras el cambio | Thomas corrigió textos (`ed7d78e`) |
| 16/10, 2:30–4:10 a. m. | Claude (Anthropic) | Dabidri escribió los prompts con los que Claude generó la Vista del comprador (catálogo) y los pedidos: ficha con pedido por kilos, seguimiento con enlace privado, cancelación, aprobación del administrador, validación de dirección, teléfono, correo y municipios del Huila, y las reglas de la base de datos contra la sobreventa | `src/pedidos.py`, `productos.py` (catálogo), `validaciones.py`, `db.py` (migración), `schema.sql` (tabla `pedidos`, vista y triggers), `comprador.html`, `pedido.html`, `pedidos.html`, `ficha.html`, `test_pedidos.py` | Dabidri: probó el flujo en el navegador; la suite quedó en 80 pruebas, todas en verde; se unió con el PR #20 | Ajustes por pasos: dirección, municipio y vereda (`edb5aa8`, `b063147`, `3633a06`) |
| 16/10, ~2:00 a. m. | Claude (Anthropic) | Revisión de buenas prácticas: encontró que la clave de sesión fija permitía falsificar una sesión de administrador; propuso y probó los arreglos y el diferenciador «precio justo sugerido» | `app.py`, `productos.py`, `respaldo.py`, `lotes.py`, `calculos.py`, plantillas de lote, 5 pruebas nuevas (`7b4bce1`) | Santiago: revisó el `git diff`, corrió las pruebas y unió el PR #19 | Se integraron con los arreglos los cambios del precio sugerido que Santiago ya había escrito |
| 16/10, ~3:00 a. m. | Claude (Anthropic) | Borradores de la documentación a partir del código real; ejecución automatizada de los casos en el navegador con capturas (19 y luego 25 con los pedidos); detectó que la ficha de un producto bloqueado mostraba kg para pedir y propuso la corrección de una línea en `ficha.html`; diagramas; script de rendimiento; respaldo de demostración | `README.md`, `ENTREGA.md`, `documentos/*`, `scripts/medir_rendimiento.py`, `datos/respaldo_demo.db`, `pitch/`, `ficha.html` (1 línea) | Equipo: revisó cada documento, completó los campos marcados y comprobó que todo coincida con la app | Los datos que la IA no podía saber (prueba de usabilidad, confirmaciones de cada integrante) los completó el equipo |

## Qué hizo cada integrante sin IA

- **Thomas Chica:** diseñó desde cero, sin IA, el esquema de la base de datos (`schema.sql`): tablas,
  restricciones, vistas y triggers. La IA solo generó las pruebas que lo verifican (`test_schema.py`).
- **Santiago Valencia:** definió con la IA la forma más sencilla de construir la aplicación con Python, Flask y
  SQLite; integró, ejecutó, depuró y subió cada parte, y coordinó las ramas y los Pull Requests. La IA
  generó también las plantillas HTML base, sin diseño, que luego se reemplazaron por Kaoka.
- **David Rojas Ipuz (Dabidri):** escribió los prompts para obtener con Claude el diseño visual (frontend), la Vista del
  comprador y los pedidos; los probó y los integró en el repositorio.
- **Todo el equipo:** decisiones de alcance y reparto, todos los commits y Pull Requests, la prueba de
  usabilidad (E06) y la defensa. Cada integrante puede explicar su módulo.

## IA dentro del producto

No aplica: Kaoka no llama a ningún modelo de IA ni servicio externo. Los cálculos son fórmulas
deterministas en `calculos.py`. Costo de IA en operación: 0 COP.

## Componentes externos

| Componente | Uso | Licencia |
| --- | --- | --- |
| Flask 3.1.3 | Framework web | BSD-3-Clause |
| Werkzeug 3.1 | Servidor de desarrollo y hash de contraseñas | BSD-3-Clause |
| Jinja2 3.1 | Plantillas HTML | BSD-3-Clause |
| Click 8 | Comandos `cargar-demo`, `respaldar`, `restaurar` | BSD-3-Clause |
| SQLite (módulo `sqlite3` de Python) | Base de datos | Dominio público |
| pytest 9.1 | Pruebas automatizadas | MIT |
| Playwright + Chromium (solo para generar evidencias, no es dependencia de la app) | Ejecución automatizada de casos y capturas | Apache-2.0 / BSD |
| Mermaid CLI (solo para dibujar diagramas) | Diagramas de E03 | MIT |

Plantillas o material previo: ninguno. Íconos: SVG propios en `_iconos.html`, generados junto con el
diseño Kaoka; Dabidri confirma que no se copiaron de una librería con licencia.
Datos: sintéticos, tomados del documento del reto (productores ficticios).
