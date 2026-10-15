import pytest

from src.calculos import calcular_merma, costo_unitario, margen


# ---------- Merma ----------

def test_merma_ejemplo_del_reto():
    assert calcular_merma(100, 80) == pytest.approx(20.0)


def test_merma_otros_valores():
    assert calcular_merma(200, 170) == pytest.approx(15.0)
    assert calcular_merma(100, 100) == pytest.approx(0.0)


def test_merma_entrada_cero_no_divide():
    assert calcular_merma(0, 0) is None


# ---------- Costo unitario ----------

def test_costo_unitario_ejemplo_del_reto():
    assert costo_unitario(1_600_000, 80) == pytest.approx(20_000.0)


def test_costo_unitario_salida_cero_no_divide():
    assert costo_unitario(1_600_000, 0) is None


# ---------- Margen ----------

def test_margen_ejemplo_del_reto():
    assert margen(25_000, 20_000) == pytest.approx(20.0)


def test_margen_negativo_si_se_vende_bajo_costo():
    # vender a 18.000 algo que cuesta 20.000 es pérdida
    assert margen(18_000, 20_000) == pytest.approx(-11.111, rel=1e-3)


def test_margen_sin_costo_es_none():
    # si la salida fue 0, el costo es None y el margen también
    assert margen(25_000, None) is None


def test_margen_precio_cero_no_divide():
    assert margen(0, 20_000) is None