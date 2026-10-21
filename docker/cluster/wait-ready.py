import json
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


def wait_ready():
    deadline = time.monotonic() + 120
    status = "Aguardando os dois workers no HDFS e no YARN."
    while time.monotonic() < deadline:
        try:
            with urlopen(
                "http://namenode:9870/jmx?qry=Hadoop:service=NameNode,name=NameNodeInfo",
                timeout=5,
            ) as response:
                hdfs = json.load(response)["beans"][0]
            with urlopen(
                "http://resourcemanager:8088/ws/v1/cluster/metrics", timeout=5
            ) as response:
                yarn = json.load(response)["clusterMetrics"]
            live_nodes = len(json.loads(hdfs["LiveNodes"]))
            if (
                live_nodes == 2
                and not hdfs["Safemode"]
                and yarn["activeNodes"] == 2
            ):
                print("HDFS e YARN prontos: dois workers registrados.", flush=True)
                return
            status = (
                f"HDFS: {live_nodes} DataNodes; "
                f"safemode={hdfs['Safemode']!r}; YARN: {yarn['activeNodes']} workers."
            )
        except (URLError, TimeoutError) as error:
            status = f"Aguardando os servicos: {error}"
        print(status, file=sys.stderr, flush=True)
        time.sleep(2)
    sys.exit(f"Cluster nao ficou pronto em 120 segundos. Ultimo estado: {status}")


if __name__ == "__main__":
    wait_ready()
