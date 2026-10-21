import math

# Índices das variáveis comparadas com a temperatura (índice 8).
# Cada nome será a chave usada para agrupar as estatísticas da comparação.
COLUNAS = {0: 'X', 1: 'Y', 4: 'FFMC', 5: 'DMC', 6: 'DC', 7: 'ISI', 9: 'RH', 10: 'wind', 11: 'rain', 12: 'area'}


def mapear(linha):
    # Valida a estrutura e converte a temperatura comum às comparações.
    # Uma temperatura não numérica impede a emissão de pares desta linha.
    if len(linha) != 13:
        return
    try:
        temperatura = float(linha[8])
    except ValueError:
        return
    # Emite por variável apenas pares numéricos finitos. As seis estatísticas
    # podem ser somadas em lotes antes do cálculo final de Pearson:
    # contagem, soma_x, soma_y, soma_x2, soma_y2 e soma_xy.
    for indice, nome in COLUNAS.items():
        try:
            valor = float(linha[indice])
        except ValueError:
            continue
        if math.isfinite(temperatura) and math.isfinite(valor):
            yield nome, (1, temperatura, valor, temperatura**2, valor**2, temperatura*valor)
