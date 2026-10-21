# Correlação de Pearson com MapReduce local

Esta é a versão da branch `main`: uma análise de correlação em Python que
simula as etapas MapReduce em um único processo. **Não utiliza Hadoop, HDFS,
Docker nem processamento distribuído.** A implementação Hadoop está na
branch `map-reduce-with-hadoop`.

## Objetivo e dados de entrada

O programa calcula a correlação de Pearson entre a temperatura e dez variáveis
do arquivo `forestfireinput.csv`: `X`, `Y`, `FFMC`, `DMC`, `DC`, `ISI`, `RH`,
`wind`, `rain` e `area`.

Cada registro deve ter 13 colunas. A temperatura está no índice 8, contando
a partir de zero. As colunas de mês e dia da semana não entram no cálculo,
pois são categóricas.

## Como executar

É necessário apenas Python 3; o projeto usa a biblioteca padrão e não exige
instalar pacotes com `pip`. Na raiz do repositório, execute:

```sh
python3 correlacao-mapreduce/executar.py correlacao-mapreduce/forestfireinput.csv
```

No Windows, com o inicializador Python:

```powershell
py correlacao-mapreduce/executar.py correlacao-mapreduce/forestfireinput.csv
```

Também é possível entrar na pasta dos scripts:

```sh
cd correlacao-mapreduce
python3 executar.py forestfireinput.csv
```

O relatório é impresso no terminal; o programa não cria arquivos de saída.
O caminho do CSV é relativo ao diretório de onde o comando foi executado.
Sem exatamente um argumento, o programa mostra a instrução de uso e termina
com código 1.

## Organização do código

| Arquivo | Responsabilidade |
| --- | --- |
| `correlacao-mapreduce/executar.py` | Lê o CSV, coordena as etapas e imprime o relatório em português. |
| `correlacao-mapreduce/mapper.py` | Valida os pares numéricos e produz estatísticas parciais por variável. |
| `correlacao-mapreduce/reducer.py` | Soma estatísticas e calcula a correlação final. |
| `correlacao-mapreduce/forestfireinput.csv` | Dataset de entrada fornecido com o projeto. |

## Fluxo de execução

1. **Leitura:** `executar.py` abre o arquivo usando `csv.reader` e codificação
   `utf-8-sig`, que aceita um marcador BOM no início do arquivo.
2. **Map:** `mapear` aceita linhas com 13 colunas, converte a temperatura
   e cada variável para números e emite uma chave por variável. Cada valor
   emitido contém `(1, x, y, x², y², xy)`, em que `x` é a temperatura
   e `y` é a variável comparada.
3. **Agrupamento local:** o dicionário `grupos` reúne as estatísticas da mesma
   variável em listas. Isso simula o agrupamento por chave de MapReduce,
   mas mantém os registros na memória da máquina.
4. **Combiner:** as listas são divididas em lotes de até 100 registros.
   `combinar` soma cada uma das seis posições das tuplas. Não calcula médias
   ou correlações parciais, evitando combinar coeficientes incorretamente.
5. **Reduce:** `reduzir` soma os lotes e calcula Pearson a partir dos totais.
   Retorna a contagem e `None` quando não há observações suficientes ou
   quando um dos termos de variância não é positivo.
6. **Relatório:** para cada variável, imprime o número de comparações, o
   coeficiente com quatro casas decimais, a classificação e a interpretação.
   Sem registros válidos, informa correlação indefinida.

## Fórmula e interpretação

As estatísticas agregadas permitem calcular Pearson sem usar as observações
individuais na etapa final:

```text
r = (n × Σxy − Σx × Σy)
    / √((n × Σx² − (Σx)²) × (n × Σy² − (Σy)²))
```

O coeficiente pertence ao intervalo `[-1, 1]`. O sinal indica a direção da
associação linear e o valor absoluto determina a classificação adotada:

| Valor absoluto de r | Classificação |
| --- | --- |
| Menor que 0,10 | Muito fraca |
| De 0,10 até menos de 0,30 | Fraca |
| De 0,30 até menos de 0,70 | Moderada |
| A partir de 0,70 | Forte |

O código limita o resultado ao intervalo teórico para conter pequenos desvios
de arredondamento. Correlação não demonstra causalidade. A classificação é
uma convenção do programa; ele não realiza teste de significância estatística.

## Pontos importantes para leitura e auditoria

- O total anunciado como “instâncias com 13 colunas” verifica apenas a
  estrutura das linhas; não garante que todos os campos sejam números válidos.
- Temperatura não numérica invalida a linha para todas as comparações.
  Valor não numérico em outra variável descarta apenas aquela comparação.
  Pares com `NaN` ou infinito não são emitidos pelo Mapper.
- A quantidade de comparações pode variar entre as variáveis. Uma linha
  de cabeçalho com 13 campos entra no total estrutural, mas não gera pares
  se a temperatura não puder ser convertida.
- A implementação armazena as estatísticas de todas as comparações em memória;
  os lotes do Combiner não tornam a leitura distribuída nem limitam essa memória.
- A fórmula usa somas de quadrados em ponto flutuante, sujeitas a perda de
  precisão para valores extremos ou quase constantes.
- Erros de acesso ao arquivo e outros erros não tratados encerram a execução
  com a mensagem de exceção do Python; não há recuperação automática.

Os comentários nos scripts descrevem os blocos de processamento para auxiliar
a revisão. Eles não representam uma auditoria formal de segurança ou qualidade.
