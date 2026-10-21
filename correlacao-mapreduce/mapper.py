import math

COLUNAS = {0: 'X', 1: 'Y', 4: 'FFMC', 5: 'DMC', 6: 'DC', 7: 'ISI', 9: 'RH', 10: 'wind', 11: 'rain', 12: 'area'}


def mapear(linha):
    if len(linha) != 13:
        return
    try:
        temperatura = float(linha[8])
    except ValueError:
        return
    for indice, nome in COLUNAS.items():
        try:
            valor = float(linha[indice])
        except ValueError:
            continue
        if math.isfinite(temperatura) and math.isfinite(valor):
            # n, soma_x, soma_y, soma_x2, soma_y2, soma_xy
            yield nome, (1, temperatura, valor, temperatura**2, valor**2, temperatura*valor)
