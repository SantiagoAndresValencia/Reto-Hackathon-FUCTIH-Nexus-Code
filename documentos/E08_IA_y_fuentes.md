# E08 · Declaración de IA y componentes externos

**Sí usamos IA generativa** durante el evento, como asistente. El producto **no** usa IA en tiempo de
ejecución. Todo el trabajo se hizo entre el 15/10 (3:00 p. m.) y el 16/10 de 2026; no hay código previo
al evento.

## Bitácora de uso de IA

| Fecha y hora (aprox.) | Herramienta | Uso y aporte relevante | Componente o archivo | Revisión humana | Corrección hecha |
| --- | --- | --- | --- | --- | --- |
| 15/10, 3:00–4:30 p. m. | Claude (Anthropic), chat | Lectura del reto, plan por horas, reparto de roles, elección | Plan de trabajo, `.gitignore` | Santiago: decidió la tecnología y el reparto con el equipo | Se ajustó el plan para 3 integrantes |
| 15/10, 4:00–11:00 p. m. | Claude | Código ayudo a las ideas del codigo para que luego se pudiera, ejecutar y subir con commits propios; explicación de cada parte | `db.py`, `validaciones.py`, `lotes.py`, `auditoria.py`, `auth.py`, `productos.py`, `respaldo.py`, `app.py`, plantillas iniciales, `conftest.py`, `test_lotes.py`, `test_auth.py`, `test_productos.py`, `test_flujo_jurado.py` | Santiago: Reviso cada parte, la ejecutó, revisó en el navegador y subió cada commit | Errores encontrados al ejecutar y corregidos: falta de `src/__init__.py`, columnas de auditoría equivocadas (error 500), tabla de lotes rota, login sin usuarios (`cargar-demo`), mensaje de error en verde |
| 15/10, tarde | Claude | Instrucciones (prompts) por rol para los compañeros | Base de datos y cálculos | Thomas y Dabidri | — |
| 15/10, tarde | Thomas | Se utilizo ia para el test_schema.py, y se utilizo la herramienta Claude (Anthropic) | `src/schema.sql`, `src/tests/test_schema.py` | Thomas | |
| 15/10, tarde | David | Se utilizo la IA para guia de diseño de los calculos.py siguiendo las recomendaciones de reto, y para el test de los calculos si se le solicito a claude que generara el test | `src/calculos.py`, `src/tests/test_calculos.py` | David  | |
| 15/10–16/10, noche | David — herramienta de IA para diseño (el repositorio ignora carpetas `.claude/`, `.codex/`, `.impeccable/`) | Diseño visual Kaoka: plantillas, estilos, íconos, consulta pública por código. Santiago preparó con Claude el contexto (roles, rutas y variables de las plantillas) para ese chat | `src/templates/*`, `src/static/kaoka.css`, `kaoka.js`, `_iconos.html`, ruta `/consultar` | Dabidri y Santiago: probaron que las rutas y los datos sigan iguales; 63 pruebas pasaban tras el cambio | Thomas corrigió textos (`ed7d78e`) |
| 16/10, ~2:00 a. m. | Claude | Revisión de buenas prácticas: encontró que la clave de sesión fija permitía falsificar una sesión de admin; propuso y probó los arreglos y el diferenciador «precio justo sugerido» | `app.py`, `productos.py`, `respaldo.py`, `lotes.py`, `calculos.py`, plantillas de lote, 5 pruebas nuevas (`7b4bce1`) | Santiago: revisó el `git diff`, corrió las pruebas y unió el PR #19 | Se juntaron sus cambios propios del precio sugerido con los arreglos |
| 16/10, ~3:00 a. m. | Claude | Borradores de la documentación a partir del código real; ejecución automatizada de los 19 casos en el navegador con capturas; diagramas; script de rendimiento; respaldo de demostración | `README.md`, `ENTREGA.md`, `documentos/*`, `scripts/medir_rendimiento.py`, `datos/respaldo_demo.db`, `pitch/` | Equipo: revisar cada documento, completar los campos marcados y comprobar que todo coincide con la app | Los campos que la IA no puede saber (prueba de usabilidad, confirmaciones de cada integrante) se dejaron en blanco a propósito |

**Qué hizo el equipo y no la IA:** decisiones de alcance y reparto; ejecución, prueba y depuración en
sus equipos; todos los commits y Pull Requests; integración de las ramas; revisión del diseño; la
prueba de usabilidad (E06) y la defensa. Cada integrante debe poder explicar su módulo.


- **Thomas:** diseñó desde cero, sin IA, el esquema de la base de datos (`schema.sql`): tablas,
  restricciones, vistas y triggers. La IA solo generó las pruebas que lo verifican (`test_schema.py`).
- **Santiago:** definió la forma más sencilla de construir la aplicación con Python, Flask y
  SQLite; integró, ejecutó, depuró y subió cada parte, y coordinó las ramas y los Pull Requests. La IA
  generó las plantillas HTML base, sin diseño, que luego se reemplazaron por Kaoka.
- **Dabidri:** escribió los prompts para obtener el diseño visual (frontend) y lo integró en el
  repositorio.
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

Plantillas o material previo: ninguno. Íconos: SVG propios en `_iconos.html`, generados junto con el diseño Kaoka (Dabidri confirma que no se copiaron de una librería con licencia).
Datos: sintéticos del documento del reto (productores ficticios).
