# Kaoka · Cacao con historia, calidad y valor

**Equipo Nexus Code** · II Hackathon de Programación USCO · Reto oficial de Agroindustria (Semillero DEVURITY)

Kaoka es un MVP web para que una asociación cacaotera del Huila (simulada) registre el cacao que recibe,
lo transforme sin consumir más de lo que tiene, calcule merma, costo y margen, decida qué productos se
venden y le muestre al comprador el origen del producto sin revelar datos internos.

- **Operador:** recibe lotes y registra transformaciones.
- **Administrador:** ve costos y márgenes, libera o bloquea productos, revisa la auditoría y exporta CSV.
- **Comprador:** consulta la ficha pública por código, sin iniciar sesión.

**Diferenciador:** *Precio justo sugerido.* Además del margen actual, Kaoka calcula el precio mínimo al
que la asociación debe vender para ganar el margen objetivo (30 %): `costo unitario ÷ (1 − 0,30)`.
Con el ejemplo del reto (20.000 COP/kg) sugiere 28.571 COP/kg. Es apoyo a la venta para que el productor
no venda a pérdida.

Índice de la entrega y matriz de trazabilidad: [ENTREGA.md](ENTREGA.md).

---

## Requisitos del entorno

| Elemento | Versión verificada |
| --- | --- |
| Python | 3 (verificado con 3.13; en el PC del stand anotar la versión con `python --version`) |
| Flask | 3.1.3 (instala Werkzeug, Jinja2, Click, itsdangerous) |
| pytest | 9.1.1 |
| Base de datos | SQLite, incluida en Python; no requiere instalación |
| Sistema | Windows 10/11, Linux o macOS |

No necesita Internet, servicios en la nube ni claves de API.

## Instalación limpia

```bash
git clone https://github.com/SantiagoAndresValencia/Reto-Hackathon-FUCTIH-Nexus-Code.git
cd Reto-Hackathon-FUCTIH-Nexus-Code
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración (sin secretos en el repositorio)

| Variable | Para qué | Ejemplo |
| --- | --- | --- |
| `CACAO_SECRET` | Firma de la cookie de sesión. Si no se define, se genera una aleatoria en cada arranque (las sesiones se cierran al reiniciar). | Windows: `set CACAO_SECRET=una-frase-larga-solo-suya` · Linux: `export CACAO_SECRET=una-frase-larga-solo-suya` |

La base de datos se crea sola en `datos/cacao.db` al arrancar (lee `src/schema.sql`).

## Cargar datos de demostración

```bash
flask --app src/app cargar-demo
```

Crea los usuarios y los tres lotes del caso:

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `operador` | `operador123` | Operador de planta |
| `admin` | `admin123` | Administrador |

| Lote | Productor ficticio | Origen | Cantidad |
| --- | --- | --- | --- |
| CAC001 | Productor A | Rivera | 100 kg |
| CAC002 | Productor B | Campoalegre | 150 kg |
| CAC003 | Productor C | Algeciras | 80 kg |

Las contraseñas son solo de demostración (datos sintéticos).

## Ejecutar

```bash
flask --app src/app run
```
Abrir <http://127.0.0.1:5000>. 


## Pruebas automatizadas

```bash
python -m pytest -v
```

68 pruebas en `src/tests/` (inventario, doble envío, cálculos, permisos, estados, ficha pública,
auditoría, CSV, respaldo y reglas de la base de datos). Resultado verificado: **68 passed**
([salida completa](documentos/evidencias/pytest_salida.txt)).

Medición de rendimiento (100 transformaciones sintéticas en una base temporal, no toca sus datos):

```bash
python scripts/medir_rendimiento.py
```

## Respaldo y restauración

```bash
flask --app src/app respaldar datos/mi_respaldo.db      
flask --app src/app restaurar datos/respaldo_demo.db    
```

`restaurar` imprime la huella esperada y la obtenida (lotes, kg recibidos, transformaciones, productos,
registros de auditoría y `PRAGMA integrity_check`) y termina con **INTEGRIDAD OK** si coinciden. Si el
archivo no existe o no es una base SQLite válida, se detiene sin tocar la base actual.

`datos/respaldo_demo.db` es el respaldo de demostración: 3 lotes, 330 kg, 2 usuarios.

## Estructura

```
src/            código (Flask): app, auth, lotes, productos, calculos, validaciones, auditoria, respaldo
src/schema.sql  tablas, restricciones CHECK, vistas y triggers (inventario e historial inmutable)
src/templates/  pantallas (Jinja) · src/static/ estilos y JS del diseño Kaoka
src/tests/      pruebas automatizadas (pytest)
scripts/        medición de rendimiento
datos/          base local (ignorada por git) y respaldo_demo.db
documentos/     E01–E03, E05–E09 (.md y .pdf), evidencias/ y diagramas/
pitch/          E09_presentacion.pdf (5 diapositivas)
```

Arquitectura: monolito modular en capas (Flask + SQLite). Las reglas de inventario, costos y permisos
se aplican en el servidor y en la base de datos, no solo en la interfaz. Detalle en
[E03](documentos/E03_diseno.md).

## Uso de inteligencia artificial (declaración obligatoria)

Usamos IA generativa como asistente durante el evento. Resumen (detalle por herramienta, archivo y
revisión humana en [E08](documentos/E08_IA_y_fuentes.md)):

| Parte | Quién la hizo | Asistencia de IA |
| --- | --- | --- |
| Plan, división del trabajo | Equipo | Claude (Anthropic) propuso el plan; el equipo decidió y ejecutó |
| `src/schema.sql`, `test_schema.py` | Thomas Chica | Declarar en E08  |
| `calculos.py`, `test_calculos.py` | Dabidri | Declarar en E08  |
| `validaciones.py`, `db.py`, `lotes.py`, `auth.py`, `productos.py`, `auditoria.py`, `respaldo.py`, `app.py`, pruebas de flujo | Santiago Valencia | Código guiado; Santiago se guio del flujo que debia llevar el backend, lo ejecutó, corrigió errores y lo subió con commits propios |
| Diseño visual Kaoka (`templates/`, `static/`) | Dabidri | Asistido por IA  |
| Revisión de seguridad, precio justo sugerido | Santiago Valencia | Claude encontró fallos y propuso el código; Santiago lo revisó y aplicó |
| Documentación E01–E09, pruebas en navegador, diagramas | Equipo |

El producto **no usa IA** en tiempo de ejecución.

## Limitaciones conocidas

- El bloqueo es por producto: un lote con varios productos se bloquea producto por producto.
- La prueba de usabilidad con una persona externa se registra en E06 (ver estado allí).
- SQLite admite una escritura a la vez: suficiente para una asociación, no para muchas simultáneas.
- Ejecución local por HTTP; para uso en red pública se requiere HTTPS.

## Licencia y componentes

Flask, Werkzeug, Jinja2 y Click (BSD-3-Clause), pytest (MIT), SQLite (dominio público).
Datos, productores y asociación son ficticios.
