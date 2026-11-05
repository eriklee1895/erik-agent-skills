"""Regressions for the OpenRouter GPT 2.6 access-path contract."""
import base64
import json
import unittest

from test_openrouter_image import OfflineTests, PNG_BYTES, mod


class GPTImage26Tests(OfflineTests):
    def test_default_aliases_submit_26_but_explicit_25_ids_stay_pinned(self):
        for model, expected in (
            ('sunburst', 'openai/gpt-image-2.6-sunburst'),
            ('flare', 'openai/gpt-image-2.6-flare'),
            ('openai/gpt-image-2.6-sunburst', 'openai/gpt-image-2.6-sunburst'),
            ('openai/gpt-image-2.6-flare', 'openai/gpt-image-2.6-flare'),
            ('openai/gpt-image-2.5-sunburst', 'openai/gpt-image-2.5-sunburst'),
            ('openai/gpt-image-2.5-flare', 'openai/gpt-image-2.5-flare'),
        ):
            with self.subTest(model=model):
                preview = json.loads(self.run_cli(
                    'generate', '--model', model, '--prompt', 'A fox',
                    '--out', str(self.out / 'fox.png'), '--dry-run'))
                self.assertEqual(preview['request']['model'], expected)
        self.api.assert_not_called()

    def test_complexity_uses_openai_provider_options_not_top_level(self):
        for model in ('sunburst', 'flare'):
            for complexity in ('low', 'medium', 'high'):
                body = self.request(model_name=model, complexity=complexity)
                self.assertEqual(body['provider'], {
                    'options': {'openai': {'complexity': complexity}}})
                self.assertNotIn('complexity', body)
        self.assertNotIn('provider', self.request())

    def test_invalid_and_unsupported_complexity_fail_before_paid_call(self):
        for model, values in (
            ('sunburst', ('auto', '', 1, [], {})),
            ('sunburst-2.5', ('low',)),
            ('banana', ('high',)), ('grok', ('medium',)), ('mai', ('low',)),
        ):
            for value in values:
                with self.subTest(model=model, complexity=value):
                    with self.assertRaisesRegex(SystemExit, 'complexity'):
                        self.request(model_name=model, complexity=value)
        self.api.assert_not_called()

    def test_static_format_controls_reject_gif_svg_and_transparent_jpeg(self):
        for output_format in ('png', 'jpeg', 'webp'):
            self.assertEqual(self.request(output_format=output_format)['output_format'],
                             output_format)
        for output_format in ('gif', 'svg', 'jpg', 'PNG', 1, [], {}):
            with self.subTest(output_format=output_format):
                with self.assertRaisesRegex(SystemExit, 'output_format'):
                    self.request(output_format=output_format)
        with self.assertRaisesRegex(SystemExit, 'transparent.*jpeg|jpeg.*transparent'):
            self.request(output_format='jpeg', background='transparent')
        for model in ('banana', 'grok', 'mai'):
            with self.subTest(model=model):
                with self.assertRaisesRegex(SystemExit, 'output_format'):
                    self.request(model_name=model, output_format='webp')
        self.api.assert_not_called()

    def test_compression_requires_explicit_jpeg_or_webp(self):
        for output_format in (None, 'png'):
            with self.subTest(output_format=output_format):
                with self.assertRaisesRegex(SystemExit, 'output_compression.*jpeg.*webp'):
                    self.request(output_format=output_format, compression=80)
        for output_format in ('jpeg', 'webp'):
            self.assertEqual(self.request(output_format=output_format, compression=0)[
                'output_compression'], 0)

    def test_cli_and_batch_preserve_format_and_complexity(self):
        for command in ('generate', 'edit'):
            with self.subTest(command=command):
                preview = json.loads(self.run_cli(
                    command, '--model', 'flare', '--prompt', 'A fox',
                    '--complexity', 'low', '--output-format', 'webp',
                    '--out', str(self.out / 'fox.png'), '--dry-run'))
                self.assertEqual(preview['request']['output_format'], 'webp')
                self.assertEqual(preview['request']['provider'], {
                    'options': {'openai': {'complexity': 'low'}}})
        bodies = self.run_batch([{'prompt': 'A fox', 'output_format': 'jpeg',
                                 'output_compression': 80, 'complexity': 'medium'}])
        self.assertEqual(bodies[0]['output_format'], 'jpeg')
        self.assertEqual(bodies[0]['provider'], {
            'options': {'openai': {'complexity': 'medium'}}})

    def test_batch_animation_controls_fail_before_any_generation(self):
        for fields in ({'output_format': 'gif'}, {'output_format': 'svg'},
                       {'frame_count': 4}, {'frame_duration_ms': 100}):
            with self.subTest(fields=fields):
                self.write_jobs([{'prompt': 'Valid'}, {'prompt': 'Animated', **fields}])
                with self.assertRaisesRegex(SystemExit, 'batch line 2:'):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()
                self.assertFalse(self.out.exists())

    def test_output_metadata_preserves_media_type_without_base64_payload(self):
        self.api.return_value = {
            'created': 1793853149,
            'data': [{'b64_json': base64.b64encode(PNG_BYTES).decode(),
                      'media_type': 'image/png'}],
            'usage': {'cost': 0.02486},
        }
        self.run_cli('generate', '--prompt', 'A fox', '--out', str(self.out / 'fox.png'))
        metadata = json.loads((self.out / 'fox.json').read_text())
        self.assertEqual(metadata['response'], {
            'created': 1793853149, 'images': [{'media_type': 'image/png'}]})
        self.assertNotIn('b64_json', json.dumps(metadata))


if __name__ == '__main__':
    unittest.main()
