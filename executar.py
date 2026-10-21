import csv
import sys
from collections import defaultdict

from mapper import COLUNAS, mapear
from reducer import classificar_correlacao, combinar, explicar_correlacao, reduzir


# Traduz as chaves internas para nomes legíveis no relatório da análise local.
nomes_portugues = {
    "X": "Posição horizontal",
    "Y": "Posição vertical",
    "FFMC": "Umidade do combustível fino",
    "DMC": "Umidade da matéria orgânica",
    "DC": "Índice de seca",
    "ISI": "Índice de propagação inicial",
    "RH": "Umidade relativa do ar",
    "wind": "Velocidade do vento",
    "rain": "Precipitação de chuva",
    "area": "Área queimada"
}


def main(caminho):
    """Executa localmente as fases Map, Shuffle, Combiner e Reduce."""
    grupos = defaultdict(list)
    linhas_validas = 0

    # Lê o CSV, conta as linhas com estrutura esperada e agrupa por variável
    # as estatísticas parciais produzidas pelo Mapper.
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:
        for linha in csv.reader(arquivo):

            if len(linha) == 13:
                linhas_validas += 1

            for coluna, estatisticas in mapear(linha):
                grupos[coluna].append(estatisticas)

    print("\n" + "=" * 75)
    print("ANÁLISE DE CORRELAÇÃO COM A TEMPERATURA")
    print("=" * 75)
    print(f"Total de instâncias com 13 colunas: {linhas_validas}")

    # Para cada variável, simula Combiner em lotes, calcula a correlação final
    # e imprime a contagem, o coeficiente e sua interpretação.
    for coluna in COLUNAS.values():

        registros = grupos[coluna]
        nome = nomes_portugues.get(coluna, coluna)

        print("\n" + "-" * 75)
        print(f"Coluna: {nome} ({coluna})")

        if not registros:
            print("Instâncias comparadas: 0")
            print("Correlação: indefinida")
            continue

        parciais = [
            combinar(registros[i:i + 100])
            for i in range(0, len(registros), 100)
        ]

        n, correlacao = reduzir(parciais)

        print(f"Instâncias comparadas: {n}")

        if correlacao is None:
            print("Correlação: indefinida")
            print("Significado: Não foi possível calcular a correlação.")
        else:
            print(f"Correlação de Pearson: {correlacao:+.4f}")
            print(f"Classificação: {classificar_correlacao(correlacao)}")
            print(f"Significado: {explicar_correlacao(correlacao)}")

    print("\n" + "=" * 75)
    print("ANÁLISE FINALIZADA")
    print("=" * 75)


if __name__ == "__main__":
    # Exige exatamente um caminho para o arquivo CSV de entrada.
    if len(sys.argv) != 2:
        print("Uso: py executar.py forestfireinput.csv")
        sys.exit(1)

    main(sys.argv[1])