"""The value-chain example must retain native direction semantics after parsing."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "evals" / "fixtures" / "semantic-value-chain.svg"


@unittest.skipUnless(shutil.which("npx"), "npx is required for parser checks")
class SemanticValueChainTests(unittest.TestCase):
    def test_structure_and_arrows_remain_native(self):
        completed = subprocess.run(
            [
                "npx", "-y", "@larksuite/whiteboard-cli@0.2.13",
                "-i", str(FIXTURE), "-f", "svg",
                "--to", "openapi", "--format", "json",
            ],
            text=True, capture_output=True, check=True,
        )
        nodes = json.loads(completed.stdout)["data"]["result"]["nodes"]
        self.assertFalse(
            {"svg", "image"} & {node["type"] for node in nodes},
            "The example must not flatten structural elements or arrowheads",
        )
        connectors = [n["connector"] for n in nodes if n["type"] == "connector"]
        arrows = [
            c for c in connectors
            if c["end"]["arrow_style"] != "none"
        ]
        # Three main edges, feedback, bypass, and two rollout edges.
        self.assertEqual(7, len(arrows))
        self.assertTrue(all(c["start"]["arrow_style"] == "none" for c in arrows))
        elbows = [c for c in arrows if c["shape"] == "right_angled_polyline"]
        self.assertEqual(2, len(elbows), "Feedback and bypass must remain elbows")
        directions = [
            (
                c["end"]["position"]["x"] - c["start"]["position"]["x"],
                c["end"]["position"]["y"] - c["start"]["position"]["y"],
            )
            for c in elbows
        ]
        self.assertTrue(any(dx < 0 for dx, _ in directions), "Feedback goes left")
        self.assertTrue(any(dx > 0 for dx, _ in directions), "Bypass goes right")

        routes = {
            (
                n["connector"]["start"]["position"]["x"],
                n["connector"]["start"]["position"]["y"],
                n["connector"]["end"]["position"]["x"],
                n["connector"]["end"]["position"]["y"],
            ): n
            for n in nodes
            if n.get("connector", {}).get("shape") == "right_angled_polyline"
        }
        # Coordinates identify the fixed fixture's stage boundaries, not just
        # arbitrary left/right arrows. Turning points are relative to node x/y.
        expected = {
            (992, 264, 560, 264): ("dash", [(992, 224), (560, 224)]),
            (560, 840, 1384, 840): ("solid", [(560, 872), (1384, 872)]),
        }
        self.assertEqual(set(expected), set(routes))
        for endpoints, (border_style, turns) in expected.items():
            with self.subTest(endpoints=endpoints):
                node = routes[endpoints]
                self.assertEqual(border_style, node["style"]["border_style"])
                actual_turns = [
                    (node["x"] + p["x"], node["y"] + p["y"])
                    for p in node["connector"]["turning_points"]
                ]
                self.assertEqual(turns, actual_turns)


if __name__ == "__main__":
    unittest.main()
