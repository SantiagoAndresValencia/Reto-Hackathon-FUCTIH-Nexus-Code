# E07 · Instalación, respaldo y mantenimiento

## Instalación limpia verificada

Instrucciones completas en el [README](../README.md). Verificado el 16/10/2026 en un entorno Linux
limpio: clon del commit `ca3d77c` → entorno virtual nuevo → `pip install -r requirements.txt` (Flask
3.1.3, Werkzeug 3.1.9, Jinja2 3.1.6, Click 8.5.0, pytest 9.1.1) → `cargar-demo` → `pytest` = **80
passed** → `flask run` y los 25 casos de E05. En Windows, igual, con `.venv\Scripts\activate`.

**Configuración sin secretos:** única variable `CACAO_SECRET` (Windows:
`set CACAO_SECRET=una-frase-larga`). El repositorio no contiene claves.

## Respaldo, restauración e integridad

| Paso | Comando | Comprobación |
| --- | --- | --- |
| Respaldar | `flask --app src/app respaldar datos/respaldo_AAAAMMDD.db` | Copia en caliente con la API de respaldo de SQLite e imprime la huella |
| Restaurar | `flask --app src/app restaurar datos/respaldo_demo.db` | Compara la huella del respaldo con la de la base restaurada: `integrity_check`, códigos de lote, total de kg recibidos y número de transformaciones, productos y registros de auditoría. Termina en **INTEGRIDAD OK** o en error |
| Protección | — | Si el archivo no existe o no es SQLite, se detiene sin tocar la base actual |

**Prueba de pérdida total (16/10):** se borró `datos/cacao.db` y se restauró `respaldo_demo.db` →
**INTEGRIDAD OK** (CAC001–CAC003, 330 kg). Con los datos de los casos de E05 el resultado fue el
mismo (`evidencias/cp17_respaldo_restauracion.txt`). Rutina: respaldo diario al cerrar, copiado a una USB.

## Servicios externos, costos y operación sin conexión

| Elemento | Estado |
| --- | --- |
| Servicios externos, nube o IA | Ninguno |
| Costo de operación en la demo | 0 COP (corre en el computador de la asociación) |
| Sin Internet | Funciona igual: servidor, base de datos, fuentes e íconos son locales. Los celulares se conectan por la red Wi-Fi local (`flask --app src/app run --host 0.0.0.0`) aunque no haya Internet |
| Si se apaga el computador | Los datos siguen en `datos/cacao.db` al volver a ejecutar la app (CP16) |

**Correcciones realizadas:** los diez fallos del desarrollo y su corrección están en E05; el más
grave, la clave de sesión fija que permitía falsificar una sesión de administrador, se corrigió en
`7b4bce1` con prueba de regresión.

## Fallos y límites conocidos

| Fallo o límite | Impacto | Cómo operar mientras tanto |
| --- | --- | --- |
| Sin `CACAO_SECRET`, la clave cambia al reiniciar | Hay que volver a iniciar sesión | Definir `CACAO_SECRET` antes de `flask run` |
| El bloqueo es por producto, no por lote completo | Varios clics si un lote tiene muchos productos | Bloquear cada producto desde el detalle del lote |
| Usuarios solo por comando | Sin cambio de contraseña desde la interfaz | Cambiar los de demostración antes de un uso real |
| HTTP local sin HTTPS; cerrar sesión es un enlace (GET) | No apto para Internet pública | Usar solo en red local; la cookie es SameSite=Lax |
| La huella de `restaurar` no cuenta los pedidos | La integridad de los pedidos no se compara automáticamente | Revisar la lista de Pedidos tras restaurar |
| SQLite admite una escritura a la vez | Suficiente para una asociación | Migrar a PostgreSQL si se agrupan varias asociaciones |

## Mejoras priorizadas para 30 días

| # | Mejora | Responsable | Esfuerzo | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| 1 | **Bloquear un lote completo** en un clic, con kg afectados | Santiago Valencia | 4 h | Dado un lote con 3 productos, cuando el administrador lo bloquea con motivo, entonces los 3 quedan bloqueados en una transacción, se ven los kg afectados y se auditan los 3 cambios |
| 2 | **QR imprimible** de la ficha para el empaque | David Rojas Ipuz (Dabidri) | 3 h | Dado P-CAC001-1, cuando se imprime su etiqueta, entonces al escanear el QR con un celular se abre su ficha pública |
| 3 | **Gestión de usuarios** y contraseñas (solo administrador) | Thomas Chica | 6 h | Dado un administrador, cuando crea un operador, entonces este puede entrar; un operador no puede crear usuarios (403); todo queda auditado |
