
UMBRAL_MERMA = 15.0  # porcentaje máximo de merma permitido
MARGEN_OBJETIVO = 30.0  # margen que la asociación quiere ganar sobre la venta


def calcular_merma(entrada, salida):
 
    if entrada is None or entrada == 0:
        return None
    return (entrada - salida) / entrada * 100


def costo_unitario(costo_total, salida):

    if salida is None or salida == 0:
        return None
    return costo_total / salida


def margen(precio, costo_unitario):

    if costo_unitario is None or precio is None or precio == 0:
        return None
    return (precio - costo_unitario) / precio * 100

def alertas_de(entrada, salida, costo_total, precio):
    """Lista de alertas (tipo, regla, causa) de una transformación."""
    alertas = []
    merma = calcular_merma(entrada, salida)
    if merma is not None and salida <= entrada and merma > UMBRAL_MERMA:
        alertas.append(("merma", f"Merma mayor a {UMBRAL_MERMA:g} %",
                        f"Merma de {merma:g} % (entrada {entrada:g} kg, salida {salida:g} kg)"))
    costo = costo_unitario(costo_total, salida)
    if costo is None:
        alertas.append(("costo", "Salida vendible igual a 0", "No se puede calcular el costo unitario"))
    elif costo >= precio:
        alertas.append(("costo", "Costo unitario mayor o igual al precio",
                        f"Costo {costo:,.0f} COP/kg frente a precio {precio:,.0f} COP/kg"))
    return alertas
