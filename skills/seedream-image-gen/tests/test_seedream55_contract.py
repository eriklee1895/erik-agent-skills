"""Seedream 5.5 request and response contract regressions (offline)."""
import base64
import json
import unittest

import test_flash_contract as legacy

picture = legacy.picture

MODEL = 'doubao-seedream-5-5-261028'


class Seedream55ContractTests(unittest.TestCase):
    setUp = legacy.FlashContractTests.setUp
    respond = legacy.FlashContractTests.respond
    invoke = legacy.FlashContractTests.invoke

    def test_default_text_to_rgba_and_opaque_reference_to_rgba(self):
        for refs in ([], ['--reference-image', str(self.reference)],
                     ['--reference-image', str(self.reference), '--reference-image', str(self.alpha)]):
            code, out, err = self.invoke('generate', '--prompt', 'isolated logo, transparent background',
                                         '--background', 'transparent', '--dry-run', *refs)
            self.assertEqual(code, 0, err)
            body = json.loads(out)
            self.assertEqual(body['model'], MODEL)
            self.assertEqual(body['background'], 'transparent')
            self.assertEqual(body['output_format'], 'png')
        self.assertEqual(self.requests, [])

    def test_auto_background_and_55_fast_rejection(self):
        code, out, err = self.invoke('generate', '--model', '5.5', '--prompt', 'logo', '--background', 'auto', '--dry-run')
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)['background'], 'auto')
        code, _, _ = self.invoke('generate', '--prompt', 'logo', '--optimize-prompt', 'fast', '--dry-run')
        self.assertNotEqual(code, 0)
        code, _, _ = self.invoke('generate', '--prompt', 'logo', '--background', 'transparent', '--output-format', 'jpeg', '--dry-run')
        self.assertNotEqual(code, 0)

    def test_layer_options_are_55_only_and_bounded(self):
        code, out, err = self.invoke('decompose', '--reference-image', str(self.reference), '--max-images', '100', '--text-recognition', '--dry-run')
        self.assertEqual(code, 0, err)
        body = json.loads(out)
        self.assertEqual(body['layer_decomposition_options'], {'max_images': 100, 'text_recognition': True})
        self.assertNotIn('background', body)
        for extra in (['--max-images', '1'], ['--max-images', '101'], ['--model', 'pro', '--text-recognition'], ['--model', 'flash', '--max-images', '10']):
            code, _, _ = self.invoke('decompose', '--reference-image', str(self.reference), '--dry-run', *extra)
            self.assertNotEqual(code, 0)
        self.assertEqual(self.requests, [])

    def test_ocr_and_high_layer_indices_survive_download_and_manifest(self):
        ocr = {'text': 'HELLO', 'lines': [{'bounding_box': {'absolute': [10, 20, 200, 60], 'normalized': [10, 20, 195, 59]},
                    'runs': [{'text': 'HELLO', 'style': {'similar_font_family': 'Arial', 'foreground_color': '#123456', 'bold': True}}]}]}
        def response(request):
            import httpx
            self.requests.append(request)
            return httpx.Response(200, json={'data': [
                {'b64_json': base64.b64encode(picture((1024, 1024), 'RGB')).decode(), 'z_index': 0, 'background': 'opaque'},
                {'b64_json': base64.b64encode(picture((256, 320))).decode(), 'z_index': 18,
                 'text_recognition': ocr, 'background': 'transparent', 'bounding_box': {'absolute': [10, 20, 210, 340]}}
            ], 'usage': {'generated_images': 2}})
        self.respond = response
        output = self.root / 'ocr-layers'
        code, _, err = self.invoke('decompose', '--reference-image', str(self.reference), '--max-images', '30',
                                    '--text-recognition', '--out-dir', str(output))
        self.assertEqual(code, 0, err)
        manifest = json.loads((output / 'layers.json').read_text())
        self.assertEqual(manifest['layers'][1]['text_recognition'], ocr)
        self.assertEqual(manifest['layers'][1]['background'], 'transparent')
        self.assertEqual(manifest['layer_decomposition_options'], {'max_images': 30, 'text_recognition': True})
        self.assertTrue((output / 'layer-018.png').is_file())
        self.assertNotIn('b64_json', (output / 'layers.json').read_text())

    def test_auto_response_background_is_recorded(self):
        original = self.respond
        def response(request):
            import httpx
            raw = original(request).json()
            raw['data'][0]['background'] = 'transparent'
            return httpx.Response(200, json=raw)
        self.respond = response
        output = self.root / 'auto.png'
        code, _, err = self.invoke('generate', '--prompt', 'logo', '--background', 'auto', '--out', str(output))
        self.assertEqual(code, 0, err)
        metadata = json.loads(output.with_suffix('.json').read_text())
        self.assertEqual(metadata['background'], 'auto')
        self.assertEqual(metadata['reported_background'], 'transparent')


if __name__ == '__main__':
    unittest.main()
