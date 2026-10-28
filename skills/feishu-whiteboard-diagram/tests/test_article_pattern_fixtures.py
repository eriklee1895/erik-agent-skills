import json
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "evals" / "fixtures"
WHITEBOARD_CLI = "@larksuite/whiteboard-cli@0.2.13"
FIXTURE_NAMES = (
    "conditional-routing.svg",
    "workflow-variants.svg",
    "overview-detail-loop.svg",
)


def native_endpoints(node):
    connector = node["connector"]
    return (
        connector["start"]["position"]["x"],
        connector["start"]["position"]["y"],
        connector["end"]["position"]["x"],
        connector["end"]["position"]["y"],
    )


@unittest.skipUnless(shutil.which("npx"), "npx is required for parser checks")
class ArticlePatternFixtureTests(unittest.TestCase):
    def _fixture(self, name):
        path = FIXTURES / name
        self.assertTrue(path.exists(), f"Missing generic pattern fixture: {name}")
        return path

    def _convert(self, name):
        completed = subprocess.run(
            [
                "npx", "-y", WHITEBOARD_CLI,
                "-i", str(self._fixture(name)), "-f", "svg",
                "--to", "openapi", "--format", "json",
            ],
            text=True, capture_output=True, check=True,
        )
        nodes = json.loads(completed.stdout)["data"]["result"]["nodes"]
        self.assertFalse(
            {"svg", "image"} & {node["type"] for node in nodes},
            "Structural elements must remain native",
        )
        return nodes

    def test_new_fixtures_pass_fit_lint_and_parser_checks(self):
        for name in FIXTURE_NAMES:
            with self.subTest(name=name):
                path = self._fixture(name)
                subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "fit_check.py"), str(path), "--json"],
                    text=True, capture_output=True, check=True,
                )
                subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "lint_svg.py"), str(path)],
                    text=True, capture_output=True, check=True,
                )
                completed = subprocess.run(
                    ["npx", "-y", WHITEBOARD_CLI, "-i", str(path), "-f", "svg", "--check"],
                    text=True, capture_output=True, check=True,
                )
                check = json.loads(completed.stdout)["data"]["check"]
                self.assertEqual(0, check["errors"], check["issues"])
                self.assertEqual(0, check["warnings"], check["issues"])

    def test_conditional_routing_preserves_native_branches_merge_and_feedback(self):
        name = "conditional-routing.svg"
        root = ET.parse(self._fixture(name)).getroot()
        criteria = root.findall(".//*[@data-role='criterion']")
        self.assertEqual(2, len(criteria), "Each route must carry its own decision criterion")

        nodes = self._convert(name)
        arrow_nodes = [
            n for n in nodes
            if n["type"] == "connector" and n["connector"]["end"]["arrow_style"] != "none"
        ]
        self.assertEqual(7, len(arrow_nodes), "Input, two branches, merge, output and feedback")
        dashed = [n for n in arrow_nodes if n.get("style", {}).get("border_style") == "dash"]
        self.assertEqual(1, len(dashed), "The failure return must remain dashed")
        feedback = dashed[0]
        self.assertEqual(
            (720, 810, 80, 265),
            native_endpoints(feedback),
            "Validation feedback must run from the common gate to the input card",
        )
        routes = {native_endpoints(n): n for n in arrow_nodes}
        self.assertIn((410, 610, 620, 700), routes, "Standard route must reach the common gate")
        self.assertIn((1030, 610, 820, 700), routes, "Complex route must reach the common gate")

    def test_workflow_variants_share_ids_geometry_and_native_arrows(self):
        name = "workflow-variants.svg"
        root = ET.parse(self._fixture(name)).getroot()
        variants = {}
        for node in root.findall(".//*[@data-node]"):
            variant = node.attrib["data-variant"]
            variants.setdefault(variant, {})[node.attrib["data-node"]] = node
        self.assertEqual({"guided", "managed"}, set(variants))
        self.assertEqual({"N1", "N2", "N3", "N4"}, set(variants["guided"]))
        self.assertEqual(set(variants["guided"]), set(variants["managed"]))

        for node_id in variants["guided"]:
            with self.subTest(node_id=node_id):
                guided = variants["guided"][node_id].attrib
                managed = variants["managed"][node_id].attrib
                self.assertEqual(guided["y"], managed["y"])
                self.assertEqual(guided["width"], managed["width"])
                self.assertEqual(guided["height"], managed["height"])
                self.assertEqual(
                    float(guided["x"]) - 80,
                    float(managed["x"]) - 760,
                    "Only the panel origin may change between variants",
                )

        nodes = self._convert(name)
        arrows = [
            n["connector"] for n in nodes
            if n["type"] == "connector" and n["connector"]["end"]["arrow_style"] != "none"
        ]
        self.assertEqual(6, len(arrows), "Three shared main-chain edges per variant")

    def test_overview_detail_preserves_representative_fanout_and_zoom(self):
        name = "overview-detail-loop.svg"
        root = ET.parse(self._fixture(name)).getroot()
        representatives = root.findall(".//*[@data-representative='ellipsis']")
        self.assertEqual(2, len(representatives), "Collapse repeated requests and workers")
        zoom = root.findall(".//*[@data-detail-for='request-b']")
        self.assertEqual(1, len(zoom), "The detail panel must have one explicit source")
        children = list(root)
        self.assertGreater(
            children.index(zoom[0]),
            children.index(root.find(".//*[@id='detail-panel']")),
            "The zoom arrow must be painted above the detail panel, not hidden by it",
        )

        nodes = self._convert(name)
        arrow_nodes = [
            n for n in nodes
            if n["type"] == "connector" and n["connector"]["end"]["arrow_style"] != "none"
        ]
        self.assertEqual(10, len(arrow_nodes), "Two fan-outs, two joins and one zoom link")
        dashed = [n for n in arrow_nodes if n.get("style", {}).get("border_style") == "dash"]
        self.assertEqual(1, len(dashed), "The zoom link is not another execution edge")
        self.assertEqual(
            (880, 335, 880, 675),
            native_endpoints(dashed[0]),
            "Zoom navigation must connect request B to its detailed coordinator",
        )


if __name__ == "__main__":
    unittest.main()
