import math
import sys


def combinar(registros):
    """Soma estatísticas parciais; a operação pode ser repetida com segurança."""
    return tuple(sum(partes) for partes in zip(*registros))


def reduzir(registros):
    """Calcula Pearson a partir das somas agregadas de uma variável."""
    n, sx, sy, sxx, syy, sxy = combinar(registros)
    # Aplica a fórmula de Pearson usando somente as somas emitidas pelo Mapper.
    # Se uma variável não variar ou houver menos de duas observações, o
    # coeficiente não pode ser definido.
    a = n * sxx - sx * sx
    b = n * syy - sy * sy
    if n < 2 or a <= 0 or b <= 0:
        return n, None
    r = (n * sxy - sx * sy) / math.sqrt(a * b)
    # Corrige apenas possíveis desvios numéricos além do intervalo teórico.
    return n, max(-1.0, min(1.0, r))


def classificar_correlacao(r):
    """Converte o coeficiente em uma descrição de intensidade e direção."""
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Muito fraca"
    elif intensidade < 0.30:
        nivel = "fraca"
    elif intensidade < 0.70:
        nivel = "moderada"
    else:
        nivel = "forte"

    return ("Positiva " if r > 0 else "Negativa ") + nivel


def explicar_correlacao(r):
    """Gera uma interpretação textual simples do sentido da associação."""
    intensidade = abs(r)

    if intensidade < 0.10:
        return "Não apresenta relação linear significativa em intensidade."
    if r > 0:
        return "Quando a temperatura aumenta, esta variável tende a aumentar."
    return "Quando a temperatura aumenta, esta variável tende a diminuir."


def _ler_registro(linha):
    """Lê uma linha intermediária no formato chave<TAB>seis estatísticas."""
    chave, valores = linha.rstrip("\r\n").split("\t", 1)
    partes = valores.split(",")
    if len(partes) != 6:
        raise ValueError("esperadas seis estatísticas")

    numeros = [float(parte) for parte in partes]
    if not all(math.isfinite(numero) for numero in numeros):
        raise ValueError("estatística não finita")
    if numeros[0] < 0 or not numeros[0].is_integer():
        raise ValueError("contagem inválida")

    return chave, (int(numeros[0]), *numeros[1:])


def _formatar_estatisticas(registros):
    """Serializa as estatísticas para a saída intermediária do Combiner."""
    return ",".join(str(valor) for valor in registros)


def processar_fluxo(entrada, saida, apenas_combinar=False):
    """Agrega chaves ordenadas e emite parciais ou resultados finais."""
    # O Hadoop agrupa os dados por chave; mantém apenas a chave e o total
    # correntes para processar o fluxo sem armazenar todos os registros.
    chave_atual = None
    total = None

    def emitir():
        """Emite o total no formato intermediário ou a correlação calculada."""
        if apenas_combinar:
            print(f"{chave_atual}\t{_formatar_estatisticas(total)}", file=saida)
            return

        n, correlacao = reduzir([total])
        if correlacao is None:
            resultado = f"Instâncias comparadas: {n}; Correlação: indefinida"
        else:
            resultado = (
                f"Instâncias comparadas: {n}; "
                f"Correlação de Pearson: {correlacao:+.4f}; "
                f"Classificação: {classificar_correlacao(correlacao)}; "
                f"Significado: {explicar_correlacao(correlacao)}"
            )
        print(f"{chave_atual}\t{resultado}", file=saida)

    # Lê e valida cada par intermediário, soma os valores da mesma chave e
    # emite o grupo ao encontrar a próxima chave ou chegar ao fim do fluxo.
    for numero_linha, linha in enumerate(entrada, start=1):
        if not linha.strip():
            continue
        try:
            chave, estatisticas = _ler_registro(linha)
        except (ValueError, OverflowError) as erro:
            raise ValueError(f"linha intermediária {numero_linha} inválida: {erro}") from erro

        if chave_atual is not None and chave != chave_atual:
            emitir()
            total = None

        chave_atual = chave
        total = estatisticas if total is None else combinar([total, estatisticas])

    if chave_atual is not None:
        emitir()


def main():
    """Seleciona o modo Combiner ou Reducer a partir dos argumentos."""
    apenas_combinar = sys.argv[1:] == ["--combine"]
    if sys.argv[1:] not in ([], ["--combine"]):
        print("Uso: reducer.py [--combine]", file=sys.stderr)
        return 2

    try:
        processar_fluxo(sys.stdin, sys.stdout, apenas_combinar)
    except ValueError as erro:
        print(erro, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
