import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "parser-contract.svg"
WHITEBOARD_CLI = "@larksuite/whiteboard-cli@0.2.13"


@unittest.skipUnless(shutil.which("npx"), "npx is required for parser contract tests")
class ParserContractTests(unittest.TestCase):
    def test_whiteboard_cli_0213_node_mapping(self):
        completed = subprocess.run(
            [
                "npx",
                "-y",
                WHITEBOARD_CLI,
                "-i",
                str(FIXTURE),
                "-f",
                "svg",
                "--to",
                "openapi",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        nodes = payload["data"]["result"]["nodes"]
        node_types = [node["type"] for node in nodes]
        self.assertEqual(1, node_types.count("svg"), "polygon mapping changed")
        self.assertEqual(1, node_types.count("connector"), "path mapping changed")

        connector = next(node for node in nodes if node["type"] == "connector")
        self.assertEqual("curve", connector["connector"]["shape"])

        gradient_node = next(
            node
            for node in nodes
            if node["type"] == "composite_shape"
            and "fill_gradient" in node.get("style", {})
        )
        stops = gradient_node["style"]["fill_gradient"]["stops"]
        self.assertEqual(["#ff0000", "#0000ff"], [stop["color"] for stop in stops])


if __name__ == "__main__":
    unittest.main()
