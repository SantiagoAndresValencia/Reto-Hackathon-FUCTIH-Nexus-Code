import math
from datetime import datetime


class ErrorValidacion(Exception):
    """Dato inválido; el mensaje se muestra al usuario."""


def texto(valor, campo):
    valor = (valor or "").strip()
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    return valor


def _a_numero(valor, campo):
    try:
        n = float(str(valor).strip().replace(",", "."))
    except ValueError:
        raise ErrorValidacion(f"El campo «{campo}» debe ser un número.") from None
    if not math.isfinite(n):
        raise ErrorValidacion(f"El campo «{campo}» debe ser un número.")
    return n


def numero_positivo(valor, campo):
    n = _a_numero(valor, campo)
    if n <= 0:
        raise ErrorValidacion(f"El campo «{campo}» debe ser mayor que 0.")
    return n


def numero_no_negativo(valor, campo):
    n = _a_numero(valor, campo)
    if n < 0:
        raise ErrorValidacion(f"El campo «{campo}» no puede ser negativo.")
    return n


def fecha(valor, campo):
    valor = texto(valor, campo)
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        raise ErrorValidacion(f"El campo «{campo}» debe ser una fecha válida (AAAA-MM-DD).") from None
    return valor