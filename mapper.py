import math
import sys

# Mapeia os índices das variáveis do CSV às chaves de saída. A temperatura,
# que serve como referência para todas as correlações, está no índice 8.
COLUNAS = {0: 'X', 1: 'Y', 4: 'FFMC', 5: 'DMC', 6: 'DC', 7: 'ISI', 9: 'RH', 10: 'wind', 11: 'rain', 12: 'area'}


def mapear(linha):
    """Valida uma linha e emite estatísticas parciais por variável numérica."""
    # Primeiro valida a estrutura da linha e converte a temperatura. Se ela
    # estiver ausente ou inválida, nenhuma correlação dessa linha é calculada.
    if len(linha) != 13:
        return
    try:
        temperatura = float(linha[8])
    except ValueError:
        return

    # Para cada variável, gera contagem, somas, quadrados e produto cruzado.
    # Esses valores são suficientes para calcular Pearson após a agregação
    # distribuída, sem precisar guardar as observações individuais.
    for indice, nome in COLUNAS.items():
        try:
            valor = float(linha[indice])
        except ValueError:
            continue
        if math.isfinite(temperatura) and math.isfinite(valor):
            yield nome, (1, temperatura, valor, temperatura**2, valor**2, temperatura*valor)


def main():
    import csv

    # Interface do Hadoop Streaming: lê registros CSV da entrada padrão e
    # escreve cada par chave-estatísticas na saída padrão.
    for linha in csv.reader(sys.stdin):
        for coluna, estatisticas in mapear(linha):
            valores = ",".join(str(valor) for valor in estatisticas)
            print(f"{coluna}\t{valores}")


if __name__ == "__main__":
    main()
