"""Integration contracts: real uv script, real Earshot, real PCM files."""

import hashlib
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "earshot_sfx.py"


class AudioEffectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="earshot-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def call(self, *args, success=True):
        p = subprocess.run(
            ["uv", "run", "--locked", "--script", str(SCRIPT), *map(str, args)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        self.last_process = p
        if success:
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout)
        return json.loads(p.stdout)

    def test_runtime_has_no_heavy_packages_or_models(self):
        r = self.call("doctor")
        self.assertTrue(r["ok"])
        self.assertEqual(r["runtime"]["forbidden_packages"], [])
        self.assertEqual(r["runtime"]["forbidden_modules_loaded"], [])
        self.assertEqual(r["runtime"]["earshot"], "0.3.0")

    def test_catalog_is_dynamic_and_filters_supported_knobs(self):
        r = self.call("list", "--category", "whoosh_fast")
        ids = [s["id"] for s in r["sounds"]]
        self.assertIn("whoosh_fast/crisp", ids)
        self.assertTrue(all(s["category"] == "whoosh_fast" for s in r["sounds"]))
        self.assertTrue(all("knobs" in s for s in r["sounds"]))

    def test_render_delivers_pcm_timing_and_reproducible_seed(self):
        args = [
            "render",
            "whoosh_fast/crisp",
            "--dur",
            "0.8",
            "--apex",
            "0.32",
            "--seed",
            "42",
            "--align",
            "peak",
            "--cue-at",
            "3.0",
        ]
        a = self.call(*args, "--out", self.root / "a.wav")
        b = self.call(*args, "--out", self.root / "b.wav")
        wav = self.root / "a.wav"
        with wave.open(str(wav)) as f:
            self.assertEqual(f.getframerate(), 48000)
            self.assertEqual(f.getnframes(), 38400)
            self.assertEqual(f.getsampwidth(), 3)
        self.assertEqual(a["audio"]["sha256"], b["audio"]["sha256"])
        self.assertEqual(
            a["audio"]["sha256"], hashlib.sha256(wav.read_bytes()).hexdigest()
        )
        self.assertLessEqual(abs(a["audio"]["peak_s"] - 0.32), 0.005)
        self.assertAlmostEqual(
            a["placement"]["start_s"] + a["placement"]["anchor_s"], 3.0, places=5
        )
        self.assertEqual(
            json.loads((self.root / "a.meta.json").read_text())["audio"], a["audio"]
        )

    def test_early_cue_preserves_negative_placement(self):
        r = self.call(
            "render",
            "whoosh_fast/crisp",
            "--dur",
            "0.8",
            "--apex",
            "0.32",
            "--align",
            "peak",
            "--cue-at",
            "0.1",
            "--out",
            self.root / "early.wav",
        )
        self.assertLess(r["placement"]["start_s"], 0)
        self.assertAlmostEqual(
            r["placement"]["start_s"] + r["placement"]["anchor_s"], 0.1, places=5
        )

    def test_refused_pitch_and_existing_output_do_not_replace_audio(self):
        target = self.root / "keep.wav"
        target.write_bytes(b"keep this")
        self.call("render", "click/soft", "--out", target, success=False)
        self.assertEqual(target.read_bytes(), b"keep this")
        self.call(
            "render",
            "whoosh_fast/crisp",
            "--pitch",
            "C5",
            "--out",
            self.root / "bad.wav",
            success=False,
        )
        self.assertFalse((self.root / "bad.wav").exists())

    def test_custom_recipe_uses_same_artifact_contract(self):
        r = self.call(
            "custom",
            "--recipe",
            SKILL / "assets" / "recipes" / "wooden_tap.py",
            "--params",
            '{"duration": 0.24, "body_hz": 180}',
            "--seed",
            "17",
            "--out",
            self.root / "wood.wav",
        )
        self.assertEqual(r["audio"]["frames"], 11520)
        self.assertEqual(r["source"]["kind"], "custom")
        self.assertEqual(r["source"]["params"]["body_hz"], 180)
        self.assertEqual(len(r["source"]["recipe_sha256"]), 64)
        self.assertEqual(
            self.call("check", self.root / "wood.wav")["audio"]["frames"], 11520
        )

    def test_invalid_custom_signal_leaves_no_output(self):
        recipe = self.root / "bad_recipe.py"
        recipe.write_text(
            "import numpy as np\ndef render(params, rng):\n    return np.array([0.0, np.nan])\n"
        )
        self.call(
            "custom", "--recipe", recipe, "--out", self.root / "bad.wav", success=False
        )
        self.assertFalse((self.root / "bad.wav").exists())

    def test_kit_has_measured_takes_and_reuses_cache(self):
        spec = self.root / "kit.json"
        spec.write_text(
            json.dumps(
                {
                    "kit": 1,
                    "name": "test",
                    "sr": 48000,
                    "roles": {
                        "click": {
                            "sound": "click/soft",
                            "takes": 2,
                            "seed": 17,
                            "align": "onset",
                        },
                        "whoosh.short": {
                            "sound": "whoosh_fast/crisp",
                            "edits": {"dur": 0.8, "apex": 0.32},
                            "align": "peak",
                        },
                    },
                }
            )
        )
        out = self.root / "takes"
        a = self.call("kit", "render", spec, "--out", out)
        self.assertEqual(len(a["assets"]), 3)
        self.assertTrue((out / "kit.lock.json").is_file())
        for take in a["assets"]:
            self.assertTrue(Path(take["file"]).is_file())
            self.assertGreater(take["dur_s"], 0)
            self.assertIn(take["align"], ("onset", "peak", "end"))
        b = self.call("kit", "render", spec, "--out", out)
        self.assertEqual(b["kit"]["stats"]["rendered"], 0)
        self.assertEqual(b["kit"]["stats"]["cached"], 3)

    def test_malformed_params_and_invalid_numbers_are_errors(self):
        for args in [
            ["render", "click/soft", "--dur", "nan"],
            ["render", "click/soft", "--dur", "-1"],
            ["render", "whoosh_fast/crisp", "--dur", "0.4", "--apex", "0.5"],
        ]:
            r = self.call(*args, "--out", self.root / "invalid.wav", success=False)
            self.assertFalse(r["ok"])
            self.assertFalse((self.root / "invalid.wav").exists())

    def test_resampling_preserves_legal_peak_target(self):
        for sound, sr in [("pluck/kalimba", 96000), ("whoosh_fast/crisp", 44100)]:
            r = self.call(
                "render",
                sound,
                "--sr",
                sr,
                "--peak-db",
                "0",
                "--out",
                self.root / f"{sr}.wav",
            )
            self.assertEqual(r["audio"]["sr"], sr)
            self.assertAlmostEqual(r["audio"]["peak_db"], 0, delta=0.01)

    def test_invalid_kit_check_is_not_success(self):
        for name, content in [
            ("missing.json", None),
            (
                "unknown.json",
                {"kit": 1, "roles": {"click": {"sound": "does-not-exist/sound"}}},
            ),
        ]:
            p = self.root / name
            if content is not None:
                p.write_text(json.dumps(content))
            r = self.call("kit", "check", p, success=False)
            self.assertFalse(r["ok"])

    def test_custom_recipe_diagnostics_do_not_corrupt_json_stdout(self):
        recipe = self.root / "verbose.py"
        recipe.write_text(
            'import numpy as np\nprint("loading recipe")\n'
            'def render(params, rng):\n    print("rendering recipe")\n'
            "    return np.sin(np.arange(2400) * (2 * np.pi * 440 / 48000))\n"
        )
        result = self.call(
            "custom", "--recipe", recipe, "--out", self.root / "verbose.wav"
        )
        self.assertEqual(result["audio"]["frames"], 2400)
        self.assertIn("loading recipe", self.last_process.stderr)
        self.assertIn("rendering recipe", self.last_process.stderr)

    def test_resampled_kit_matches_unclipped_single_render_and_caches(self):
        spec = self.root / "kit.json"
        spec.write_text(
            json.dumps(
                {
                    "kit": 1,
                    "sr": 96000,
                    "roles": {
                        "click": {
                            "sound": "pro_click/glass",
                            "seed": 42,
                            "edits": {"peak_db": 0},
                        }
                    },
                }
            )
        )
        out = self.root / "takes"
        kit_result = self.call("kit", "render", spec, "--out", out)
        asset = kit_result["assets"][0]
        expected = self.call(
            "render",
            "pro_click/glass",
            "--seed",
            asset["seed"],
            "--peak-db",
            "0",
            "--sr",
            "96000",
            "--out",
            self.root / "single.wav",
        )
        self.assertEqual(asset["sha256"], expected["audio"]["sha256"])
        take = json.loads((out / "kit.lock.json").read_text())["roles"]["click"][
            "takes"
        ][0]
        for key in ("onset_s", "peak_s", "end_s", "dur_s", "peak_db", "lufs_m_max"):
            self.assertEqual(take[key], asset[key], key)
        self.assertEqual(
            take["sha1"], hashlib.sha1(Path(asset["file"]).read_bytes()).hexdigest()
        )
        cached = self.call("kit", "render", spec, "--out", out)
        self.assertEqual(cached["kit"]["stats"]["rendered"], 0)
        self.assertEqual(cached["assets"][0]["sha256"], asset["sha256"])

    def test_legacy_resampled_kit_cache_is_regenerated(self):
        spec = self.root / "kit.json"
        spec.write_text(
            json.dumps(
                {
                    "kit": 1,
                    "sr": 96000,
                    "roles": {
                        "click": {
                            "sound": "pro_click/glass",
                            "seed": 42,
                            "edits": {"peak_db": 0},
                        }
                    },
                }
            )
        )
        out = self.root / "takes"
        first = self.call("kit", "render", spec, "--out", out)
        lock_path = out / "kit.lock.json"
        legacy = json.loads(lock_path.read_text())
        legacy.pop("skill_renderer_revision", None)
        lock_path.write_text(json.dumps(legacy))
        migrated = self.call("kit", "render", spec, "--out", out)
        self.assertEqual(migrated["kit"]["stats"]["rendered"], 1)
        self.assertEqual(migrated["assets"][0]["sha256"], first["assets"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
