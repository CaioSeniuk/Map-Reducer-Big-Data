import csv
import sys
from collections import defaultdict

from mapper import COLUNAS, mapear
from reducer import combinar, reduzir


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


def classificar_correlacao(r):
    # Verifica a intensidade da correlação
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Muito fraca"
    elif intensidade < 0.30:
        nivel = "fraca"
    elif intensidade < 0.70:
        nivel = "moderada"
    else:
        nivel = "forte"

    # Verifica a direção da correlação
    if r > 0:
        return "Positiva " + nivel
    else:
        return "Negativa " + nivel


def explicar_correlacao(r):
    # Explica o significado do resultado
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Não apresenta relação linear significativa em intensidade."

    if r > 0:
        return "Quando a temperatura aumenta, esta variável tende a aumentar."
    else:
        return "Quando a temperatura aumenta, esta variável tende a diminuir."


def main(caminho):
    grupos = defaultdict(list)
    linhas_validas = 0

    # Lê todas as instâncias do CSV
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:
        for linha in csv.reader(arquivo):

            if len(linha) == 13:
                linhas_validas += 1

            # Mapper: gera dados para cada comparação
            for coluna, estatisticas in mapear(linha):
                grupos[coluna].append(estatisticas)

    print("\n" + "=" * 75)
    print("ANÁLISE DE CORRELAÇÃO COM A TEMPERATURA")
    print("=" * 75)
    print(f"Total de instâncias com 13 colunas: {linhas_validas}")

    # Processa cada coluna numérica
    for coluna in COLUNAS.values():

        registros = grupos[coluna]
        nome = nomes_portugues.get(coluna, coluna)

        print("\n" + "-" * 75)
        print(f"Coluna: {nome} ({coluna})")

        if not registros:
            print("Instâncias comparadas: 0")
            print("Correlação: indefinida")
            continue

        # Combiner: agrega os dados em lotes de até 100
        parciais = [
            combinar(registros[i:i + 100])
            for i in range(0, len(registros), 100)
        ]

        # Reducer: reúne os dados e calcula Pearson
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


# Início da execução do programa
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Uso: py executar.py forestfireinput.csv")
        sys.exit(1)

    main(sys.argv[1])

# py executar.py forestfireinput.csv