from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


class AnimationIOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import animation_io
        cls.io = animation_io

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def frames(self):
        result = []
        for x in [3, 14, 25]:
            frame = Image.new("RGBA", (48, 40), (0, 0, 0, 0))
            ImageDraw.Draw(frame).rectangle((x, 8, x + 13, 25), fill=(220, 70, 20, 180))
            result.append(frame)
        return result

    def test_lossless_webp_preserves_alpha_timing_and_plays(self):
        animation = self.io.Animation(self.frames(), [30, 70, 130], 3)
        path = self.root / "loop.webp"
        meta = self.io.encode_animation(animation, path, webp_mode="lossless")
        decoded = self.io.load_frames(path)
        self.assertEqual(decoded.durations, animation.durations)
        self.assertEqual(decoded.plays, 3)
        self.assertEqual(meta["cycle_ms"], 230)
        for expected, actual in zip(animation.frames, decoded.frames):
            self.assertEqual(expected.getchannel("A").tobytes(), actual.getchannel("A").tobytes())

    def test_gif_repeat_mapping_includes_single_play(self):
        for plays in [0, 1, 4]:
            path = self.root / f"loop-{plays}.gif"
            self.io.encode_animation(self.io.Animation(self.frames(), [30, 70, 130], plays), path)
            self.assertEqual(self.io.inspect_animation(path)["plays"], plays)

    def test_gif_to_webp_keeps_variable_timeline_and_repeats(self):
        source = self.root / "source.gif"
        self.io.encode_animation(self.io.Animation(self.frames(), [30, 70, 130], 4), source)
        before = self.io.load_frames(source)
        target = self.root / "converted.webp"
        self.io.encode_animation(before, target, webp_mode="lossless")
        after = self.io.load_frames(target)
        self.assertEqual(after.durations, before.durations)
        self.assertEqual(after.plays, before.plays)

    def test_duplicate_frame_merge_preserves_duration(self):
        frames = self.frames()
        animation = self.io.Animation([frames[0], frames[0], frames[1]], [100, 200, 300])
        meta = self.io.encode_animation(animation, self.root / "merged.webp", webp_mode="lossless")
        self.assertEqual(meta["cycle_ms"], 600)
        self.assertGreaterEqual(meta["unique_frames"], 2)

    def test_gif_rounds_cumulative_time(self):
        durations = self.io.timeline(16, duration_ms=1800, format="gif")
        self.assertEqual(sum(durations), 1800)
        self.assertTrue(all(value > 0 and value % 10 == 0 for value in durations))

    def test_incompatible_dimensions_fail(self):
        animation = self.io.Animation([self.frames()[0], Image.new("RGBA", (10, 10))], [100, 100])
        with self.assertRaises(ValueError):
            self.io.encode_animation(animation, self.root / "bad.webp")

    def test_static_output_is_rejected(self):
        frame = self.frames()[0]
        path = self.root / "still.webp"
        with self.assertRaises(ValueError):
            self.io.encode_animation(self.io.Animation([frame, frame.copy()], [100, 100]), path)
        self.assertFalse(path.exists())

    def test_existing_output_is_preserved(self):
        path = self.root / "existing.webp"
        path.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            self.io.encode_animation(self.io.Animation(self.frames(), [100] * 3), path)
        self.assertEqual(path.read_bytes(), b"preserve")

    def test_byte_limit_is_enforced_without_publishing(self):
        path = self.root / "too-large.webp"
        with self.assertRaises(ValueError):
            self.io.encode_animation(self.io.Animation(self.frames(), [100] * 3), path, max_bytes=1)
        self.assertFalse(path.exists())

    def test_non_divisible_sheet_uses_actual_dimensions(self):
        image = Image.new("RGBA", (1254, 1254), "red")
        frames = self.io.split_sheet(image, (4, 4), 16, (256, 256))
        self.assertEqual(len(frames), 16)
        self.assertTrue(all(frame.size == (256, 256) for frame in frames))

    def test_nearest_neighbor_preserves_pixel_palette(self):
        image = Image.new("RGBA", (4, 2), "red")
        image.putpixel((1, 0), (0, 0, 255, 255))
        frames = self.io.split_sheet(image, (2, 1), 2, (7, 7), resample=Image.Resampling.NEAREST)
        self.assertEqual(set(frames[0].get_flattened_data()), {(255, 0, 0, 255), (0, 0, 255, 255)})

    def test_existing_metadata_is_preserved(self):
        path = self.root / "existing.webp"
        sidecar = path.with_suffix(".webp.json")
        sidecar.write_text("preserve")
        with self.assertRaises(FileExistsError):
            self.io.encode_animation(self.io.Animation(self.frames(), [100] * 3), path)
        self.assertEqual(sidecar.read_text(), "preserve")

    def test_directory_order_and_size_validation(self):
        self.frames()[0].save(self.root / "frame-02.png")
        self.frames()[1].save(self.root / "frame-01.png")
        animation = self.io.load_frames(self.root)
        self.assertEqual(len(animation.frames), 2)
        self.assertEqual(animation.frames[0].getpixel((15, 10))[0], 220)

    def test_saved_masters_retain_variable_timing(self):
        folder = self.root / "masters"
        self.io.save_frames(self.frames(), folder, durations=[30, 70, 130], plays=3)
        restored = self.io.load_frames(folder)
        self.assertEqual(restored.durations, [30, 70, 130])
        self.assertEqual(restored.plays, 3)

    def test_green_key_preserves_white_subject_pixels(self):
        frame = Image.new("RGBA", (16, 16), "#00ff00")
        ImageDraw.Draw(frame).rectangle((5, 5, 10, 10), fill="white")
        keyed = self.io.key_background(frame, "green")
        self.assertEqual(keyed.getpixel((0, 0))[3], 0)
        self.assertEqual(keyed.getpixel((7, 7)), (255, 255, 255, 255))

    def test_base_alignment_stabilizes_transparent_subject(self):
        first = Image.new("RGBA", (80, 80))
        second = Image.new("RGBA", (80, 80))
        ImageDraw.Draw(first).rectangle((20, 30, 40, 55), fill="orange")
        ImageDraw.Draw(second).rectangle((25, 24, 45, 49), fill="blue")
        aligned = self.io.align_base([first, second])
        self.assertEqual(aligned[0].getchannel("A").getbbox(), aligned[1].getchannel("A").getbbox())

    def test_base_alignment_requires_transparent_background(self):
        with self.assertRaises(ValueError):
            self.io.align_base([Image.new("RGBA", (30, 30), "white")])


if __name__ == "__main__":
    unittest.main()
