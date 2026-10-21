#!/usr/bin/env bash
set -euo pipefail

input=/dados/correlacao/input/forestfireinput.csv
output=/dados/correlacao/output
local_output=/workspace/saida-correlacao-cluster

case "${1:-run}" in
  run)
    python3 /cluster/wait-ready.py
    if hdfs dfs -test -e "$output"; then
      echo "A saida $output ja existe no HDFS. Renomeie-a antes de executar novamente." >&2
      exit 1
    fi
    cd /workspace
    hdfs dfs -mkdir -p /dados/correlacao/input
    hdfs dfs -put -f forestfireinput.csv "$input"
    exec hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.1.jar \
      -D mapreduce.framework.name=yarn \
      -D mapreduce.job.name=correlacao-cluster \
      -D mapreduce.job.reduces=2 \
      -D mapreduce.input.lineinputformat.linespermap=130 \
      -D stream.map.input.ignoreKey=true \
      -files mapper.py,reducer.py \
      -inputformat org.apache.hadoop.mapred.lib.NLineInputFormat \
      -input "$input" \
      -output "$output" \
      -mapper "python3 mapper.py" \
      -combiner "python3 reducer.py --combine" \
      -reducer "python3 reducer.py"
    ;;
  results)
    exec hdfs dfs -cat "$output/part-*"
    ;;
  export)
    if [[ -e "$local_output" ]]; then
      echo "A pasta $local_output ja existe. Renomeie-a antes de exportar." >&2
      exit 1
    fi
    exec hdfs dfs -get "$output" "$local_output"
    ;;
  *)
    echo "Uso: job.sh {run|results|export}" >&2
    exit 2
    ;;
esac
