import math
from datetime import datetime


class ErrorValidacion(Exception):
    """Excepción para errores de validación de datos."""
    pass


def texto(valor, campo):
    
    valor = (valor or "").strip()
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    return valor


def _a_numero(valor, campo):
    """Convierte a número. Acepta coma decimal: '12,5' -> 12.5"""
    try:
        n = float(str(valor).strip().replace(",", "."))
    except ValueError:
        raise ErrorValidacion(f"El campo «{campo}» debe ser un número.")
    if not math.isfinite(n):
        raise ErrorValidacion(f"El campo «{campo}» debe ser un número.")
    return n


def numero_positivo(valor, campo):
    """Número mayor que cero (por ejemplo, cantidad recibida o entrada)."""
    n = _a_numero(valor, campo)
    if n <= 0:
        raise ErrorValidacion(f"El campo «{campo}» debe ser mayor que 0.")
    return n


def numero_no_negativo(valor, campo):
    """Número que puede ser 0 pero no negativo (por ejemplo, salida o costo)."""
    n = _a_numero(valor, campo)
    if n < 0:
        raise ErrorValidacion(f"El campo «{campo}» no puede ser negativo.")
    return n


def fecha(valor, campo):
    """Fecha con formato AAAA-MM-DD que exista en el calendario."""
    valor = texto(valor, campo)
    try:
        datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        raise ErrorValidacion(f"El campo «{campo}» debe ser una fecha válida (AAAA-MM-DD).")
    return valor