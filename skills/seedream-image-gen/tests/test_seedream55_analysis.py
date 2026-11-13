"""Check metrics and coordinate reconstruction used to substantiate the report."""
import contextlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

SPEC = importlib.util.spec_from_file_location('analyze_seedream55', Path(__file__).resolve().parents[1] / 'evals' / 'analyze_seedream55.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class Seedream55AnalysisTests(unittest.TestCase):
    def test_signed_drift_and_thresholds_use_channel_differences(self):
        a = np.full((2, 2, 3), 250, dtype=np.float32)
        b = a - 10
        result = analysis.difference(a, b)
        self.assertEqual(result['mae'], 10)
        self.assertEqual(result['mean_signed_delta'], -10)
        self.assertEqual(result['changed_gt8_fraction'], 1)
        self.assertEqual(result['changed_gt32_fraction'], 0)
        self.assertAlmostEqual(result['psnr_db'], 28.1308036)

    def test_target_changes_are_excluded_from_protected_region(self):
        a = np.zeros((4, 4, 3), dtype=np.float32)
        b = a.copy()
        b[0, 0] = 255
        mask = np.ones((4, 4), dtype=bool)
        mask[0, 0] = False
        result = analysis.difference(a, b, mask)
        self.assertEqual(result['mae'], 0)
        self.assertEqual(result['exact_pixel_fraction'], 1)
        self.assertIsNone(result['psnr_db'])

    def test_reconstruction_resizes_crop_to_base_bbox_and_honors_omission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new('RGB', (100, 80), 'white').save(root / 'base.png')
            Image.new('RGBA', (200, 200), (255, 0, 0, 255)).save(root / 'crop.png')
            record = {'name':'fixture','assets':[
                {'file':'crop.png','z_index':3,'bounding_box':{'absolute':[10,20,30,40]}},
                {'file':'base.png','z_index':0}]}
            composed = analysis.compose(root, record)
            self.assertEqual(composed.size, (100, 80))
            self.assertEqual(composed.getpixel((10,20)), (255,0,0,255))
            self.assertEqual(composed.getpixel((30,40)), (255,255,255,255))
            self.assertEqual(analysis.compose(root, record, omit=[3]).getpixel((10,20)), (255,255,255,255))

    def test_failed_run_still_emits_counts_and_null_latency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new('RGB', (100,80), 'white').save(root/'fixture.png')
            source = root/'source-product'
            source.mkdir()
            (source/'result.json').write_text(json.dumps({'name':'source-product','status':'error','model':'doubao-seedream-5-5-261028'}))
            with contextlib.redirect_stdout(io.StringIO()):
                analysis.main(root)
            result = json.loads((root/'analysis.json').read_text())
            self.assertEqual(result['request_count'], 1)
            self.assertEqual(result['success_count'], 0)
            self.assertEqual(result['latency']['pro'], {'count':0, 'api_median_ms':None})


if __name__ == '__main__':
    unittest.main()
