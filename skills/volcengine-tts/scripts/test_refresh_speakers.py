# skills/volcengine-tts/scripts/test_refresh_speakers.py
"""Tests for refresh-speakers.build_speakers_md curated quick reference."""
import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "refresh-speakers.py"
spec = importlib.util.spec_from_file_location("refresh_speakers_tts", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _spk(vt, scene, heat=0, name=None, typ="bigtts", langs=None):
    return {
        "voice_type": vt, "name": name or vt, "type": typ,
        "gender": "女", "age": "", "scene": scene, "description": "d",
        "languages": langs or [], "trial_url": "https://example.com/t.wav",
        "heat": heat, "status": "online", "emoji": "",
    }


def test_scene_order_narration_first():
    """客服/教学靠前，角色扮演靠后，其他垫底（与 seed-audio 创作向相反）"""
    speakers = [
        _spk("a", "角色扮演"), _spk("b", "通用场景", heat=5),
        _spk("c", "客服场景"), _spk("d", "教学场景"),
        _spk("e", "其他"), _spk("f", "视频配音"),
    ]
    md = mod.build_speakers_md(speakers)
    headers = [line for line in md.splitlines() if line.startswith("## ")]
    scene_names = [h.split("（")[0].replace("## ", "") for h in headers]
    assert scene_names[0] == "客服场景"
    assert scene_names[1] == "教学场景"
    assert scene_names.index("其他") == len(scene_names) - 1
    assert scene_names.index("客服场景") < scene_names.index("教学场景") < scene_names.index("通用场景")
    assert scene_names.index("通用场景") < scene_names.index("视频配音") < scene_names.index("角色扮演")


def test_top_n_truncation_per_scene():
    """每个场景最多列 TOP_VOICES_PER_SCENE 行，但标注总数"""
    speakers = [_spk(f"v{i}", "教学场景", heat=100 - i) for i in range(12)]
    md = mod.build_speakers_md(speakers)
    assert "本场景共 12 个" in md
    assert f"列 Top {mod.TOP_VOICES_PER_SCENE}" in md
    rows = [l for l in md.splitlines() if l.startswith("| v")]
    assert len(rows) == mod.TOP_VOICES_PER_SCENE
    assert "v0" in rows[0]


def test_curated_header_does_not_claim_full():
    """头部声明精选速查、全量在 json 且勿读，不再自称 full voice list"""
    md = mod.build_speakers_md([_spk("a", "通用场景")])
    assert "精选" in md
    assert "speakers.json" in md
    assert "请勿把 speakers.json 读进上下文" in md
    assert "volcengine-tts.py --list-speakers" in md
    assert "Full voice list" not in md
    assert "（精选）" in md


def test_source_note_override():
    md = mod.build_speakers_md(
        [_spk("a", "通用场景")],
        source_note="数据来源：seed-audio 2026-08-27 快照，待 refresh",
    )
    assert "seed-audio 2026-08-27" in md
    assert "待 refresh" in md


def test_list_speakers_request_pins_seed_tts_2():
    """ListSpeakers 必须带 resource_ids=['seed-tts-2.0']，避免混入 1.0 音色"""
    kw = mod.list_speakers_request_kwargs(3)
    assert kw["page"] == 3
    assert kw["resource_ids"] == ["seed-tts-2.0"]
    assert mod.LIST_RESOURCE_IDS == ["seed-tts-2.0"]


def test_md_filename_is_volcengine_speakers():
    assert mod.SPEAKERS_MD.name == "volcengine-speakers.md"
    assert mod.SPEAKERS_JSON.name == "speakers.json"


def test_description_newlines_collapsed_in_table():
    speakers = [_spk("v1", "客服场景", name="营销小楠 2.0")]
    speakers[0]["description"] = "偏低沉的暖女中音。\n讲起营销策略。"
    md = mod.build_speakers_md(speakers)
    rows = [l for l in md.splitlines() if "营销小楠" in l]
    assert len(rows) == 1
    assert rows[0].startswith("| ")
    assert "讲起营销策略" in rows[0]
