"""Tests for refresh-speakers.build_speakers_md curated TTS quick reference."""
import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "refresh-speakers.py"
spec = importlib.util.spec_from_file_location("refresh_speakers", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _spk(vt, scene, heat=0, name=None):
    return {
        "voice_type": vt, "name": name or vt, "type": "bigtts",
        "gender": "女", "age": "", "scene": scene, "description": "d",
        "languages": [], "trial_url": "https://example.com/t.wav",
        "heat": heat, "status": "online", "emoji": "",
    }


def test_scene_order_narration_first():
    """通用场景排第一，教学/客服先于角色扮演，其他垫底"""
    speakers = [
        _spk("a", "角色扮演"), _spk("b", "通用场景", heat=5),
        _spk("c", "客服场景"), _spk("d", "教学场景"),
        _spk("e", "其他"), _spk("f", "视频配音"),
    ]
    md = mod.build_speakers_md(speakers)
    headers = [line for line in md.splitlines() if line.startswith("## ")]
    scene_names = [h.split("（")[0].replace("## ", "") for h in headers]
    assert scene_names[0] == "通用场景"
    assert scene_names[1] == "教学场景"
    assert scene_names.index("其他") == len(scene_names) - 1
    assert scene_names.index("教学场景") < scene_names.index("客服场景") < scene_names.index("视频配音") < scene_names.index("角色扮演")


def test_top_n_truncation_per_scene():
    """每个场景最多列 TOP_VOICES_PER_SCENE 行，但标注总数"""
    speakers = [_spk(f"v{i}", "教学场景", heat=100 - i) for i in range(12)]
    md = mod.build_speakers_md(speakers)
    assert "本场景共 12 个" in md
    assert f"列 Top {mod.TOP_VOICES_PER_SCENE}" in md
    rows = [l for l in md.splitlines() if l.startswith("| v")]
    assert len(rows) == mod.TOP_VOICES_PER_SCENE
    assert "v0" in rows[0]


def test_curated_header_is_tts_not_full_dump():
    md = mod.build_speakers_md([_spk("a", "通用场景")])
    assert "seed-tts-2.0" in md
    assert "精选" in md
    assert "speakers.json" in md
    assert "volcengine-tts.py" in md
    assert "type=bigtts" in md
    assert "（精选）" in md
    assert "seed-audio-1.0 音色速查" not in md
