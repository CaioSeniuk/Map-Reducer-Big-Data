import csv
import io
from pathlib import Path
import subprocess
import unittest

from mapper import mapear
from reducer import processar_fluxo


ROOT = Path(__file__).resolve().parents[1]


class ClusterIntegrationTest(unittest.TestCase):
    """Requires a running cluster and a completed correlation job."""

    def run_client(self, *arguments):
        return subprocess.run(
            [
                "docker", "compose", "-f", "docker/compose.cluster.yaml",
                "run", "--rm", "-T", "cliente", *arguments,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )

    def test_existing_hdfs_output_is_not_overwritten(self):
        result = self.run_client("run")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("ja existe no HDFS", result.stderr)

    def test_hdfs_results_match_local_pipeline(self):
        with (ROOT / "forestfireinput.csv").open(newline="", encoding="utf-8") as source:
            mapped = [
                f"{key}\t{','.join(str(value) for value in values)}\n"
                for row in csv.reader(source)
                for key, values in mapear(row)
            ]
        expected = io.StringIO()
        processar_fluxo(sorted(mapped, key=lambda line: line.split("\t", 1)[0]), expected)
        result = self.run_client("results")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            sorted(result.stdout.splitlines()),
            sorted(expected.getvalue().splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
