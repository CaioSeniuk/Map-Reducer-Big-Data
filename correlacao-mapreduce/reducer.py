import math


def combinar(registros):
    """Soma as estatisticas, sem calcular medias ou correlacoes parciais."""
    # Agrupa posições equivalentes das tuplas e soma cada estatística.
    # O resultado conserva o formato de entrada para novas agregações.
    return tuple(sum(partes) for partes in zip(*registros))


def reduzir(registros):
    # Consolida os lotes e obtém os termos de variância da fórmula de Pearson.
    # sx representa a soma das temperaturas; sy, a soma da variável comparada.
    n, sx, sy, sxx, syy, sxy = combinar(registros)
    a = n * sxx - sx * sx
    b = n * syy - sy * sy
    # Sem duas observações ou variância positiva, Pearson é indefinido.
    # Nos demais casos, calcula o coeficiente e limita desvios de arredondamento.
    if n < 2 or a <= 0 or b <= 0:
        return n, None
    r = (n * sxy - sx * sy) / math.sqrt(a * b)
    return n, max(-1.0, min(1.0, r))
