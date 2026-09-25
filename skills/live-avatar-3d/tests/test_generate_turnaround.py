import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'generate_turnaround.py'
spec = importlib.util.spec_from_file_location('generate_turnaround', SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f'No turnaround generator at {SCRIPT}')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TurnaroundGeneratorTests(unittest.TestCase):
    def test_prompt_locks_character_notes_and_four_views(self):
        prompt = module.build_prompt('violet round glasses and a striped scarf')
        lower = prompt.lower()
        for term in ('violet round glasses', 'front', 'three-quarter', 'profile', 'back', 'same character'):
            self.assertIn(term, lower)

    def test_official_credentials_are_accepted(self):
        self.assertEqual(
            module.resolve_credentials({'OPENAI_API_KEY': 'test-key'}),
            ('test-key', None),
        )

    def test_custom_credentials_must_be_a_pair(self):
        with self.assertRaisesRegex(ValueError, 'must be set together'):
            module.resolve_credentials({'CUSTOM_OPENAI_API_KEY': 'test-key'})

    def test_output_collision_is_rejected_before_request(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            output = Path(directory) / 'turnaround.png'
            source.write_bytes(b'source')
            output.write_bytes(b'prior result')
            with self.assertRaisesRegex(FileExistsError, 'already exists'):
                module.check_paths(source, output, force=False)

    def test_source_cannot_be_overwritten_as_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            source.write_bytes(b'source')
            with self.assertRaisesRegex(ValueError, 'must differ'):
                module.check_paths(source, source, force=True)


if __name__ == '__main__':
    unittest.main()
