"""Regression checks for the illustrative orchestrator-swimlane fixture only."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "evals" / "fixtures" / "orchestrator-swimlane.svg"

# Exact coordinates pin this example, not user-generated diagrams. Universal
# invariants are native arrows, real source directions, and no invented routes.
@unittest.skipUnless(shutil.which("npx"), "npx is required for parser checks")
class OrchestratorSwimlaneTests(unittest.TestCase):
    def test_native_arrows_badges_and_routes_survive_parsing(self):
        self.assertTrue(FIXTURE.is_file(), "The orchestrator swimlane fixture is missing")
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
            "Fixture regression: structural shapes and arrowheads must remain editable",
        )

        badge_nodes = sorted(
            (
                node
                for node in nodes
                if node["type"] == "text_shape"
                and node.get("x") == 398
                and node.get("text", {}).get("text") in {"1", "2", "3", "4", "5"}
            ),
            key=lambda node: node["y"],
        )
        self.assertEqual(
            ["1", "2", "3", "4", "5"],
            [node["text"]["text"] for node in badge_nodes],
            "Fixture regression: the example's five badges must stay ordered",
        )

        arrows = [
            node["connector"]
            for node in nodes
            if node["type"] == "connector"
            and node["connector"]["end"]["arrow_style"] != "none"
        ]
        self.assertEqual(10, len(arrows), "Fixture regression: directed-edge count changed")
        self.assertTrue(
            all(c["start"]["arrow_style"] == "none" for c in arrows),
            "Fixture regression: example arrows must remain one-directional",
        )

        def endpoints(connector):
            return (
                connector["start"]["position"]["x"],
                connector["start"]["position"]["y"],
                connector["end"]["position"]["x"],
                connector["end"]["position"]["y"],
            )

        routes = {endpoints(c): c for c in arrows}
        vertical_main_chain = {
            (596, 420, 596, 480),
            (596, 590, 596, 650),
            (596, 790, 596, 850),
        }
        self.assertTrue(
            vertical_main_chain <= set(routes),
            "Fixture regression: the example's vertical stage connectors changed",
        )

        expected_cross_lane = {
            (264, 355, 376, 355),
            (816, 535, 940, 535),
            (940, 705, 816, 705),
            (816, 900, 1264, 900),
            (376, 1055, 264, 1055),
        }
        self.assertTrue(
            expected_cross_lane <= set(routes),
            "Fixture regression: cross-lane requests or responses changed direction",
        )
        self.assertIn(
            (1058, 595, 1058, 650),
            routes,
            "Fixture regression: the data-service processing arrow changed direction",
        )

        return_endpoints = (1388, 970, 816, 1055)
        matching_returns = [
            node
            for node in nodes
            if node["type"] == "connector"
            and endpoints(node["connector"]) == return_endpoints
        ]
        self.assertEqual(
            1,
            len(matching_returns),
            f"Fixture regression: expected one decision-return route at {return_endpoints}",
        )
        result_return_node = matching_returns[0]
        result_return = result_return_node["connector"]
        self.assertEqual(
            "right_angled_polyline",
            result_return["shape"],
            "Fixture regression: the decision return must remain an elbow",
        )
        self.assertEqual(
            [(1388, 1055)],
            [
                (result_return_node["x"] + p["x"], result_return_node["y"] + p["y"])
                for p in result_return["turning_points"]
            ],
            "Fixture regression: the example returns below its request channel",
        )


if __name__ == "__main__":
    unittest.main()
