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
Compose (Linux). No Windows 10/11, habilite o WSL2 e use o Docker Desktop
em modo de contêineres Linux. A imagem atende computadores Intel/AMD
(`linux/amd64`) e ARM (`linux/arm64`); o Docker seleciona a arquitetura
automaticamente. Na raiz do projeto — a pasta que contém `mapper.py`,
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

### Erro de arquitetura da imagem (`exec format error`)

Se o Docker informar que a imagem é `linux/arm64`, mas o computador é
`linux/amd64`, a imagem baixada não é compatível com a arquitetura do
computador. Isso pode ocorrer quando a imagem foi publicada a partir de um
Mac com Apple Silicon sem incluir a versão AMD64.

Para construir a imagem localmente para a arquitetura do computador e
executar o job, use os mesmos comandos no PowerShell, macOS ou Linux:

```sh
docker compose -f docker/compose.yaml build --pull correlacao
docker compose -f docker/compose.yaml run --rm --pull never correlacao
```

A construção baixa Python, Java e Hadoop e pode levar alguns minutos.
`--pull never` no segundo comando mantém a imagem construída localmente em
vez de baixar novamente a imagem incompatível. Não é necessário alterar o
Dockerfile nem fixar `platform: linux/arm64` no Compose.

Para quem mantém a imagem publicada, a solução é publicar a tag para as
duas arquiteturas. Com acesso de escrita ao repositório no Docker Hub e um
builder Buildx com suporte a ambas as plataformas, execute na raiz do projeto:

```sh
docker login
docker buildx create --name correlacao-multiarch --driver docker-container
docker buildx build --builder correlacao-multiarch --platform linux/amd64,linux/arm64 -t caiohseniuk/projeto-big-data-hadoop:v01 --push docker
```

Se o builder `correlacao-multiarch` já existir, pule o comando de criação.
Após a publicação multi-arquitetura, o `docker pull` seleciona a variante
compatível com cada computador.

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
- `docker/compose.yaml`: seleciona a imagem publicada ou permite construí-la
  localmente, monta o projeto em `/workspace` e configura o job Hadoop
  Streaming.
- `docker/.dockerignore`: mantém os arquivos de código e os dados fora do
  contexto usado para construir a imagem.

## Simular um cluster Hadoop no computador

O arquivo `docker/compose.cluster.yaml` cria um cluster separado do modo
local anterior, com HDFS e YARN:

```text
Docker no seu computador
  namenode          -> metadados do HDFS
  resourcemanager   -> agendamento das tarefas pelo YARN
  worker1           -> DataNode + NodeManager
  worker2           -> DataNode + NodeManager
  cliente           -> envio do CSV, submissão do job e leitura dos resultados
```

Os workers são nós lógicos, não computadores físicos. O Hadoop distribui
dados e tarefas entre os contêineres, mas todos compartilham CPU, memória e
disco do computador. Não há ganho de hardware em relação a uma única máquina.
O agendador decide onde cada tarefa roda; não há afinidade fixa entre uma
divisão de entrada e um worker.

### Requisitos e inicialização

Use Docker Compose v2 com suporte a `up --wait`. No Docker Desktop, reserve
preferencialmente **8 GB de RAM e 4 CPUs** para o Docker. O cluster limita
cada coordenador a 1 GB e cada worker a 2 GB; o cliente pode usar mais 1 GB.
No Windows 10/11, use WSL2 e contêineres Linux. Execute os comandos abaixo
na raiz do projeto; funcionam também no PowerShell.

Primeiro, obtenha a imagem:

```sh
docker pull caiohseniuk/projeto-big-data-hadoop:v01
```

Se preferir construir a imagem localmente:

```sh
docker compose -f docker/compose.cluster.yaml build --pull cliente
```

Inicie os quatro serviços permanentes e aguarde seus healthchecks:

```sh
docker compose -f docker/compose.cluster.yaml up -d --wait
docker compose -f docker/compose.cluster.yaml ps
```

O cliente tem um profile separado: só é iniciado quando solicitado
explicitamente. O NameNode é formatado apenas quando seu volume ainda não
tem metadados. O HDFS usa replicação 2, guardando uma cópia em cada DataNode.
As opções de memória do YARN deixam espaço nos workers para os serviços
Java; a abertura do módulo `java.lang` permite usar os componentes Hadoop
3.4.1 com Java 17.

### Executar e obter os resultados

```sh
docker compose -f docker/compose.cluster.yaml run --rm cliente
```

O cliente espera até 120 segundos por dois DataNodes e dois NodeManagers
registrados e pelo HDFS fora do modo de segurança. Depois envia o CSV para
`/dados/correlacao/input/forestfireinput.csv` no HDFS e submete o job ao YARN.
Os scripts Python são enviados por `-files`; não precisam estar montados nos
workers.

Para demonstrar vários Mappers com este CSV pequeno, apenas o job do cluster
usa `NLineInputFormat`, com **130 linhas por divisão de entrada**. O CSV atual
de 517 linhas gera quatro divisões e dois reducers. Isso é didático: para
dados grandes, normalmente usam-se divisões maiores e o formato padrão
`TextInputFormat`. O agendador pode executar tarefas em paralelo ou em
sequência, conforme os recursos livres. A opção `stream.map.input.ignoreKey`
evita enviar o deslocamento da linha como parte do CSV ao Mapper.

Leia os resultados no HDFS:

```sh
docker compose -f docker/compose.cluster.yaml run --rm cliente results
```

Exporte-os para `saida-correlacao-cluster/` no computador:

```sh
docker compose -f docker/compose.cluster.yaml run --rm cliente export
```

A exportação recusa sobrescrever uma pasta local existente. Os resultados
do modo local original em `saida-correlacao/` não são alterados.

### Acompanhar o cluster

| Endereço | O que mostra |
|---|---|
| `http://localhost:9870` | HDFS, dois DataNodes e arquivos armazenados |
| `http://localhost:8088` | YARN, dois NodeManagers e aplicações submetidas |

Enquanto o job estiver rodando, a página da aplicação no YARN permite
acompanhar o ApplicationMaster. Este exemplo não inclui JobHistoryServer:
o acompanhamento detalhado dessa página pode deixar de estar disponível
depois que o ApplicationMaster termina.

Confira os nós e a replicação pela linha de comando:

```sh
docker compose -f docker/compose.cluster.yaml exec namenode hdfs dfsadmin -report
docker compose -f docker/compose.cluster.yaml exec resourcemanager yarn node -list
docker compose -f docker/compose.cluster.yaml exec namenode hdfs fsck /dados/correlacao/input -files -blocks -locations
```

Veja os logs se algum serviço não ficar saudável ou o job falhar:

```sh
docker compose -f docker/compose.cluster.yaml logs --tail 100
docker compose -f docker/compose.cluster.yaml logs --tail 100 worker1 worker2
```

Os logs das tarefas ficam em `/data/yarn/logs` no volume de cada worker.
Os arquivos de trabalho são mantidos por dez minutos depois do fim das
tarefas para ajudar no diagnóstico.

Com o cluster ativo e o job concluído, um teste de integração compara as
dez linhas do HDFS com o pipeline Python de referência e verifica que uma
nova execução não sobrescreve a saída. Para executá-lo, com Python 3
instalado no computador:

```sh
python3 -m unittest discover -s tests -p "test_cluster.py"
```

No Windows, use `py` no lugar de `python3`.

### Executar novamente e parar

A saída `/dados/correlacao/output` não pode existir antes de um novo job.
Para preservá-la e executar novamente:

```sh
docker compose -f docker/compose.cluster.yaml exec namenode hdfs dfs -mv /dados/correlacao/output /dados/correlacao/output-anterior
docker compose -f docker/compose.cluster.yaml run --rm cliente
```

Escolha outro nome se `output-anterior` já existir. Para exportar novamente,
renomeie também a pasta local `saida-correlacao-cluster` antes da exportação.

Pare e remova os contêineres, preservando os volumes e os dados:

```sh
docker compose -f docker/compose.cluster.yaml down
```

Para **apagar todo o HDFS e os logs deste cluster**, use
`docker compose -f docker/compose.cluster.yaml down -v`. Na próxima
inicialização, um novo HDFS será criado. As pastas já exportadas para o
computador não são apagadas.

Este cluster é exclusivamente didático: não tem autenticação, alta
disponibilidade ou proteção para produção. As interfaces web são publicadas
somente em `127.0.0.1`, e as portas internas ficam na rede Docker. Não exponha
esses serviços na internet ou em uma rede não confiável.

## Executar com Hadoop instalado na máquina (sem Docker)

Esta opção executa o mesmo job Hadoop Streaming diretamente no computador. São
necessários Hadoop com o JAR de Streaming, Java e Python 3. Execute os comandos
na raiz do projeto — a pasta que contém `mapper.py`, `reducer.py` e
`forestfireinput.csv`.

Primeiro, confirme que Hadoop e Python estão disponíveis:

```sh
hadoop version
python3 --version
```

Localize o JAR do Hadoop Streaming que corresponde à versão instalada. Por
exemplo, com Hadoop 3.4.1 e `HADOOP_HOME` configurado:

```sh
export STREAMING_JAR="$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar"
test -f "$STREAMING_JAR" && echo "Streaming JAR encontrado: $STREAMING_JAR"
```

Em macOS com Hadoop instalado pelo Homebrew, o caminho do Hadoop normalmente
pode ser definido assim:

```sh
export HADOOP_HOME="$(brew --prefix hadoop)/libexec"
export STREAMING_JAR="$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar"
```

Se sua versão ou local de instalação for diferente, ajuste o caminho do JAR.
Depois, inicie o job em modo local (MapReduce executado por Hadoop nesta
máquina, sem cluster ou HDFS):

```sh
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.framework.name=local \
  -D mapreduce.job.reduces=2 \
  -files mapper.py,reducer.py \
  -input forestfireinput.csv \
  -output saida-correlacao \
  -mapper "python3 mapper.py" \
  -combiner "python3 reducer.py --combine" \
  -reducer "python3 reducer.py"
```

O Hadoop envia os scripts para as tarefas via `-files`, executa o Mapper,
Combiner e Reducers, e grava os resultados em `saida-correlacao/part-*`.
Confira o sucesso no log (`Job ... completed successfully`) e leia os
resultados:

```sh
cat saida-correlacao/part-*
```

O diretório de saída precisa ainda não existir. Para executar novamente,
renomeie os resultados anteriores ou escolha outro valor para `-output`.

### Executar em cluster Hadoop com HDFS

Para usar um cluster, ele precisa estar iniciado e o usuário precisa ter
acesso ao HDFS. Envie o CSV para o HDFS:

```sh
hdfs dfs -mkdir -p /user/$USER/correlacao/input
hdfs dfs -put forestfireinput.csv /user/$USER/correlacao/input/
```

Execute o job sem a configuração de modo local e com caminhos HDFS:

```sh
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.job.reduces=2 \
  -files mapper.py,reducer.py \
  -input /user/$USER/correlacao/input/forestfireinput.csv \
  -output /user/$USER/correlacao/output \
  -mapper "python3 mapper.py" \
  -combiner "python3 reducer.py --combine" \
  -reducer "python3 reducer.py"
```

Consulte a saída do cluster com:

```sh
hdfs dfs -cat /user/$USER/correlacao/output/part-*
```

Os nós que executam as tarefas precisam ter Python 3 disponível. No Windows,
para executar Hadoop diretamente, recomenda-se usar uma distribuição Linux via
WSL; a opção Docker descrita acima evita configurar Hadoop e Java no Windows.

## Executar a versão Python local

Para rodar a versão de referência sem Hadoop:

```sh
python3 executar.py forestfireinput.csv
```

Esse script usa Mapper/Combiner/Reducer em Python, mas mantém e agrupa os
registros na memória do processo local; ele não inicia um job Hadoop.
