import csv
import sys
from collections import defaultdict

from mapper import COLUNAS, mapear
from reducer import combinar, reduzir


# Traduz as chaves do Mapper para os nomes apresentados no relatório.
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
    # Classifica a intensidade pelo valor absoluto, independentemente do sinal.
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Muito fraca"
    elif intensidade < 0.30:
        nivel = "fraca"
    elif intensidade < 0.70:
        nivel = "moderada"
    else:
        nivel = "forte"

    # Acrescenta a direção da associação às classes acima de "Muito fraca".
    if r > 0:
        return "Positiva " + nivel
    else:
        return "Negativa " + nivel


def explicar_correlacao(r):
    # Produz a interpretação textual conforme intensidade e direção.
    # Essa descrição não corresponde a um teste de significância estatística.
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Não apresenta relação linear significativa em intensidade."

    if r > 0:
        return "Quando a temperatura aumenta, esta variável tende a aumentar."
    else:
        return "Quando a temperatura aumenta, esta variável tende a diminuir."


def main(caminho):
    # A execução local guarda as estatísticas de todas as variáveis em memória
    # para simular o agrupamento por chave das etapas MapReduce.
    grupos = defaultdict(list)
    linhas_validas = 0

    # Lê o CSV e conta as linhas com 13 campos, mesmo se houver valores inválidos.
    # O Mapper faz a validação numérica e seus pares são agrupados por variável.
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:
        for linha in csv.reader(arquivo):

            if len(linha) == 13:
                linhas_validas += 1

            for coluna, estatisticas in mapear(linha):
                grupos[coluna].append(estatisticas)

    # Apresenta o total estrutural antes dos resultados de cada comparação.
    print("\n" + "=" * 75)
    print("ANÁLISE DE CORRELAÇÃO COM A TEMPERATURA")
    print("=" * 75)
    print(f"Total de instâncias com 13 colunas: {linhas_validas}")

    # Percorre as variáveis na ordem definida pelo Mapper e apresenta também
    # as comparações sem registros, cujo coeficiente é indefinido.
    for coluna in COLUNAS.values():

        registros = grupos[coluna]
        nome = nomes_portugues.get(coluna, coluna)

        print("\n" + "-" * 75)
        print(f"Coluna: {nome} ({coluna})")

        if not registros:
            print("Instâncias comparadas: 0")
            print("Correlação: indefinida")
            continue

        # Simula o Combiner em lotes de até 100; o Reducer soma esses parciais
        # e calcula Pearson sobre o conjunto completo, não sobre médias de lotes.
        parciais = [
            combinar(registros[i:i + 100])
            for i in range(0, len(registros), 100)
        ]

        n, correlacao = reduzir(parciais)

        print(f"Instâncias comparadas: {n}")

        # Distingue correlação indefinida de coeficiente calculado e formata
        # classificação e interpretação para o relatório.
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


# Exige um único caminho de entrada antes de iniciar a execução local.
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Uso: py executar.py forestfireinput.csv")
        sys.exit(1)

    main(sys.argv[1])

# py executar.py forestfireinput.csv