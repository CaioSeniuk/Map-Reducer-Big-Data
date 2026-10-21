# Correlação de Pearson com Hadoop Streaming

Este projeto calcula a correlação de Pearson entre a temperatura e as
variáveis numéricas do arquivo `forestfireinput.csv`, usando Hadoop MapReduce
com Hadoop Streaming. O Mapper, o Combiner e o Reducer são scripts Python.

## O que o cálculo faz

A temperatura está na coluna de índice `8` do CSV (os índices começam em
zero). Para cada linha válida, o programa compara essa temperatura com as
variáveis `X`, `Y`, `FFMC`, `DMC`, `DC`, `ISI`, `RH`, `wind`, `rain` e `area`.
Cada comparação resulta em uma correlação independente.

Pearson produz um coeficiente entre `-1` e `+1`: valores positivos indicam
associação linear positiva; valores negativos, associação negativa; e valores
próximos de zero, uma associação linear fraca. O resultado não demonstra
causalidade. O programa também atribui uma classificação de intensidade
(muito fraca, fraca, moderada ou forte).

## Como o MapReduce é executado

Ao executar `docker compose -f docker/compose.yaml run --rm correlacao`, o
Compose inicia um container temporário a partir da imagem
`caiohseniuk/projeto-big-data-hadoop:v01`. A imagem fornece Python, Java e
Hadoop; ela não contém os fontes nem o CSV. O Compose monta a pasta do projeto
do computador como `/workspace` no container, para o job poder ler os arquivos
e gravar os resultados diretamente no computador.

O comando configurado no Compose inicia o Hadoop Streaming em **modo local**.
Isso executa o mecanismo MapReduce do Hadoop nesta máquina, mas não configura
um cluster nem distribui o processamento entre vários computadores. O job
está configurado com dois reducers.

As etapas do job são:

1. **Leitura e divisão da entrada:** o Hadoop abre
   `/workspace/forestfireinput.csv` e entrega as linhas do arquivo ao Mapper.
   Neste exemplo o arquivo tem 517 registros e, por ser pequeno, é processado
   em uma divisão de entrada.
2. **Map (`mapper.py`):** para cada linha com 13 colunas, converte a
   temperatura e os valores das variáveis para números. Linhas com estrutura
   ou temperatura inválida são ignoradas; um valor inválido em uma variável
   descarta apenas aquela comparação. Para cada valor válido, o Mapper emite
   a chave da variável e seis estatísticas:
   `n, soma_temperatura, soma_valor, soma_temperatura², soma_valor²,
   soma_temperatura×valor`. Por exemplo, uma observação da variável `RH`
   começa como a chave `RH` e as estatísticas correspondentes à temperatura
   e à umidade relativa daquela linha.
3. **Combiner (`reducer.py --combine`):** agrega por soma os valores emitidos
   para a mesma chave antes de enviá-los adiante. No log da execução de
   exemplo, os 5.170 pares do Mapper foram reduzidos a 10 registros
   combinados. O Hadoop pode chamar essa etapa zero, uma ou várias vezes;
   como ela somente soma estatísticas, isso não altera o resultado.
4. **Shuffle, ordenação e particionamento:** o Hadoop agrupa os registros
   pela chave (variável) e encaminha cada grupo a um dos dois reducers. Esse
   agrupamento é feito pelo Hadoop, não pelo código Python.
5. **Reduce (`reducer.py`):** o mesmo script é executado sem o argumento
   `--combine`. Ele soma os parciais de cada grupo, aplica a fórmula de
   Pearson às estatísticas agregadas e emite uma linha com a contagem, o
   coeficiente, a classificação e a interpretação. Se não houver dados
   suficientes ou uma variável não variar, informa correlação indefinida.
6. **Gravação da saída:** os reducers escrevem arquivos `part-*` dentro de
   `/workspace/saida-correlacao`. Como `/workspace` é a pasta montada do
   projeto, esses arquivos aparecem em `saida-correlacao/` no computador.

Em resumo, o fluxo é:

```text
forestfireinput.csv
        │
        ▼
Mapper Python: estatísticas parciais por variável
        │
        ▼
Combiner: soma parcial local por chave (opcional no Hadoop)
        │
        ▼
Shuffle/Sort/Partitioner do Hadoop: agrupa e encaminha cada variável
        │
        ▼
Reducer Python: Pearson, classificação e interpretação
        │
        ▼
saida-correlacao/part-*
```

O cálculo da correlação usa as somas agregadas, não precisa guardar todas as
observações no Reducer. Para cada variável, com `n` observações, `x` como
temperatura e `y` como o valor da variável, a fórmula é:

```text
r = (n × Σxy − Σx × Σy)
    / √((n × Σx² − (Σx)²) × (n × Σy² − (Σy)²))
```

## Executar com Docker

Instale e inicie o Docker Desktop (Windows/macOS) ou Docker Engine e Docker
Compose (Linux). Na raiz do projeto — a pasta que contém `mapper.py`,
`reducer.py`, `forestfireinput.csv` e a pasta `docker/` — execute:

```sh
docker pull caiohseniuk/projeto-big-data-hadoop:v01
docker compose -f docker/compose.yaml run --rm correlacao
```

O `docker pull` baixa a imagem. O comando `docker compose ... run` cria o
container temporário e executa o job completo; `--rm` remove o container ao
terminar, mas mantém a imagem e os resultados. Não é necessário instalar
Python, Java ou Hadoop diretamente no computador.

Quando o job terminar corretamente, o log contém `Job ... completed
successfully` e `map 100% reduce 100%`. Para verificar os resultados:

```sh
cat saida-correlacao/part-*
```

No Windows PowerShell, pode-se usar:

```powershell
Get-Content saida-correlacao/part-*
```

O diretório de saída precisa **não existir antes** de iniciar o job. Hadoop
não sobrescreve resultados anteriores. Para guardar os resultados existentes
e rodar de novo em macOS/Linux:

```sh
mv saida-correlacao saida-correlacao-anterior
docker compose -f docker/compose.yaml run --rm correlacao
```

No PowerShell:

```powershell
Rename-Item saida-correlacao saida-correlacao-anterior
docker compose -f docker/compose.yaml run --rm correlacao
```

O aviso `Unable to load native-hadoop library` pode aparecer em macOS e não
impede a execução: as bibliotecas Java padrão são usadas como alternativa.

### Usar outro arquivo CSV

Coloque o arquivo CSV na raiz do projeto e passe o caminho dentro de
`/workspace`. O arquivo precisa seguir o mesmo formato esperado: 13 colunas e
temperatura no índice 8.

```sh
docker compose -f docker/compose.yaml run --rm correlacao jar \
  /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar \
  -D mapreduce.framework.name=local \
  -D mapreduce.job.reduces=2 \
  -files mapper.py,reducer.py \
  -input /workspace/meus-dados.csv \
  -output /workspace/saida-personalizada \
  -mapper "python3 mapper.py" \
  -combiner "python3 reducer.py --combine" \
  -reducer "python3 reducer.py"
```

## O que cada arquivo faz

- `mapper.py`: valida cada linha CSV e gera as estatísticas parciais para
  cada variável; também implementa a interface de entrada/saída do Hadoop
  Streaming.
- `reducer.py`: soma estatísticas, calcula a correlação e implementa os
  modos Combiner (`--combine`) e Reducer.
- `executar.py`: versão local de referência, sem Hadoop; simula as etapas
  agrupando os dados em memória.
- `docker/Dockerfile`: define a imagem com Python, Java e Hadoop.
- `docker/compose.yaml`: seleciona a imagem publicada, monta o projeto em
  `/workspace` e configura o job Hadoop Streaming.
- `docker/.dockerignore`: mantém os arquivos de código e os dados fora do
  contexto usado para construir a imagem.

## Executar sem Docker

Para rodar a versão local de referência (não executa o Hadoop):

```sh
python3 executar.py forestfireinput.csv
```

Esse script usa Mapper/Combiner/Reducer em Python, mas mantém e agrupa os
registros na memória do processo local. Para Hadoop Streaming sem Docker,
instale Python 3, Java e Hadoop com o JAR de Streaming. O job pode rodar em
modo local ou em cluster; no cluster, configure o HDFS, use os caminhos HDFS
em `-input` e `-output` e remova `-D mapreduce.framework.name=local`. Em ambos
os casos, o caminho de saída precisa apontar para um diretório inexistente.
