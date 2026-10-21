#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HADOOP_CONF_DIR"
cp -a /opt/hadoop/etc/hadoop/. "$HADOOP_CONF_DIR/"
cp /cluster/conf/*.xml "$HADOOP_CONF_DIR/"

case "${1:-}" in
  namenode)
    if [[ ! -f /data/hdfs/name/current/VERSION ]]; then
      hdfs namenode -format -nonInteractive
    fi
    exec hdfs namenode
    ;;
  resourcemanager)
    exec yarn resourcemanager
    ;;
  worker)
    mkdir -p /data/hdfs/data /data/yarn/local /data/yarn/logs
    hdfs datanode &
    datanode_pid=$!
    yarn nodemanager &
    nodemanager_pid=$!

    cleanup() {
      kill "$datanode_pid" "$nodemanager_pid" 2>/dev/null || true
      wait "$datanode_pid" "$nodemanager_pid" 2>/dev/null || true
    }
    trap cleanup EXIT
    trap 'exit 143' TERM
    trap 'exit 130' INT
    set +e
    wait -n "$datanode_pid" "$nodemanager_pid"
    status=$?
    set -e
    echo "Um servico do worker terminou (status $status); encerrando o worker." >&2
    if [[ "$status" -eq 0 ]]; then
      status=1
    fi
    exit "$status"
    ;;
  cliente)
    shift
    exec bash /cluster/job.sh "$@"
    ;;
  *)
    echo "Uso: start.sh {namenode|resourcemanager|worker|cliente}" >&2
    exit 2
    ;;
esac
