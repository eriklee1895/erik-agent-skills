from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import composition


class CompositionTests(unittest.TestCase):
    def test_overlay_keeps_source_and_draws_new_pixels(self):
        image = Image.new("RGBA", (160, 120), "white")
        before = image.tobytes()
        result = composition.overlays([image], [{"text": "HELLO", "box": [0, 0, 1, 0.3], "font_size": 16}])
        self.assertEqual(image.tobytes(), before)
        self.assertNotEqual(result[0].tobytes(), before)

    def test_bad_region_is_rejected(self):
        with self.assertRaises(ValueError):
            composition.rectangle([0.9, 0, 0.3, 0.3], (100, 100))

    def test_background_then_caption_overlays(self):
        image = Image.new("RGBA", (160, 120), "white")
        result = composition.overlays([image], [{"text": "", "box": [0, 0, 1, 0.3], "fill": "orange"},
                                               {"text": "HELLO", "box": [0, 0, 1, 0.3], "font_size": 16}])
        self.assertNotEqual(result[0].tobytes(), image.tobytes())

    def test_missing_caption_glyphs_are_rejected(self):
        face = ImageFont.load_default(size=20)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latin.ttf"
            path.write_bytes(face.path.getvalue())
            with self.assertRaises(ValueError):
                composition.font_for("请求", 20, path)

    def test_static_region_stays_fixed(self):
        first = Image.new("RGBA", (120, 120), "white")
        second = Image.new("RGBA", (120, 120), "blue")
        frames = composition.static_composite([first, second], [0.4, 0.4, 0.2, 0.2])
        self.assertEqual(frames[0].getpixel((0, 0)), frames[1].getpixel((0, 0)))
        self.assertNotEqual(frames[0].getpixel((60, 60)), frames[1].getpixel((60, 60)))

    def test_breathing_has_bounded_visible_motion(self):
        image = Image.new("RGBA", (128, 128))
        ImageDraw.Draw(image).ellipse((35, 30, 90, 100), fill="orange")
        frames = composition.breathing_frames(image, [0.2, 0.15, 0.6, 0.75], 12)
        self.assertEqual(len(frames), 12)
        self.assertGreater(len({frame.tobytes() for frame in frames}), 1)
        self.assertEqual(frames[0].getpixel((0, 0)), frames[3].getpixel((0, 0)))

    def test_fixed_flow_has_requested_canvas(self):
        frames = composition.flow_frames((480, 270))
        self.assertEqual(len(frames), 48)
        self.assertTrue(all(frame.size == (480, 270) for frame in frames))


if __name__ == "__main__":
    unittest.main()
