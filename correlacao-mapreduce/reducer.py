import math


def combinar(registros):
    """Soma as estatisticas, sem calcular medias ou correlacoes parciais."""
    return tuple(sum(partes) for partes in zip(*registros))


def reduzir(registros):
    n, sx, sy, sxx, syy, sxy = combinar(registros)
    a = n * sxx - sx * sx
    b = n * syy - sy * sy
    if n < 2 or a <= 0 or b <= 0:
        return n, None
    r = (n * sxy - sx * sy) / math.sqrt(a * b)
    return n, max(-1.0, min(1.0, r))
