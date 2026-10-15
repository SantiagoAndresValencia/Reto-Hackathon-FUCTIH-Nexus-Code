"""Cálculos de trazabilidad del cacao: merma, costo unitario y margen.
No usa base de datos: recibe números y devuelve números.
No redondea; el redondeo se hace al mostrar en pantalla."""

UMBRAL_MERMA = 15.0  # porcentaje máximo de merma permitido


def calcular_merma(entrada, salida):
    """Porcentaje de producto que se pierde en una transformación.
    Fórmula: (entrada - salida) / entrada * 100
    Devuelve None si la entrada es 0 o no existe (no se puede dividir)."""
    if entrada is None or entrada == 0:
        return None
    return (entrada - salida) / entrada * 100


def costo_unitario(costo_total, salida):
    """Cuánto cuesta cada kg que sale de la transformación.
    Fórmula: costo_total / salida
    Devuelve None si la salida es 0 (no se puede dividir entre cero)."""
    if salida is None or salida == 0:
        return None
    return costo_total / salida


def margen(precio, costo_unitario):
    """Porcentaje del precio de venta que queda como ganancia.
    Fórmula: (precio - costo_unitario) / precio * 100
    Devuelve None si falta el costo o si el precio es 0."""
    if costo_unitario is None or precio is None or precio == 0:
        return None
    return (precio - costo_unitario) / precio * 100