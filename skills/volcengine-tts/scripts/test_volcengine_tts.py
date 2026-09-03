# skills/volcengine-tts/scripts/test_volcengine_tts.py
"""Tests for volcengine-tts query_speakers filter/sort (local catalog)."""
import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "volcengine-tts.py"
spec = importlib.util.spec_from_file_location("volcengine_tts", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_query_speakers_filter_scene():
    """按 scene 精确匹配，并按 heat 降序排序"""
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "视频配音", "heat": 50, "languages": []},
        {"voice_type": "b", "name": "B", "type": "bigtts", "scene": "通用场景", "heat": 100, "languages": []},
        {"voice_type": "c", "name": "C", "type": "icl", "scene": "视频配音", "heat": 80, "languages": []},
    ]
    result = mod.query_speakers(speakers, filters={"scene": "视频配音"}, sort_by="heat")
    assert len(result) == 2
    assert result[0]["name"] == "C"


def test_query_speakers_filter_type_bigtts():
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "通用场景", "heat": 50, "languages": []},
        {"voice_type": "b", "name": "B", "type": "icl", "scene": "通用场景", "heat": 100, "languages": []},
    ]
    result = mod.query_speakers(speakers, filters={"type": "bigtts"}, sort_by=None)
    assert len(result) == 1
    assert result[0]["type"] == "bigtts"


def test_query_speakers_filter_lang_contains():
    """lang 对 languages[] 做 contains，不是精确等于整个数组"""
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "s", "heat": 1, "languages": ["zh-cn", "ja"]},
        {"voice_type": "b", "name": "B", "type": "bigtts", "scene": "s", "heat": 2, "languages": ["en"]},
        {"voice_type": "c", "name": "C", "type": "icl", "scene": "s", "heat": 3, "languages": ["ja"]},
    ]
    result = mod.query_speakers(speakers, filters={"lang": "ja"}, sort_by="heat")
    assert [s["name"] for s in result] == ["C", "A"]


def test_query_speakers_no_filter():
    speakers = [{"voice_type": "a", "name": "A", "type": "bigtts", "scene": "s", "heat": 1, "languages": []}]
    result = mod.query_speakers(speakers, filters=None, sort_by=None)
    assert len(result) == 1


def test_query_speakers_combined_filters():
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "教学场景", "heat": 10, "languages": ["zh-cn"]},
        {"voice_type": "b", "name": "B", "type": "icl", "scene": "教学场景", "heat": 90, "languages": ["zh-cn"]},
        {"voice_type": "c", "name": "C", "type": "bigtts", "scene": "客服场景", "heat": 80, "languages": ["zh-cn"]},
    ]
    result = mod.query_speakers(
        speakers, filters={"scene": "教学场景", "type": "bigtts"}, sort_by="heat"
    )
    assert len(result) == 1
    assert result[0]["name"] == "A"


def test_no_unsigned_openapi_list_path():
    """错误的未签名 OpenAPI ListSpeakers 路径必须删除"""
    src = Path(__file__).parent.joinpath("volcengine-tts.py").read_text(encoding="utf-8")
    assert "LIST_SPEAKERS_ENDPOINT" not in src
    assert "open.volcengineapi.com" not in src
    assert 'LIST_SPEAKERS_VERSION = "2024-01-01"' not in src
    assert 'data.get("Response", {}).get("Speakers"' not in src
    assert "def _builtin_speakers" not in src
