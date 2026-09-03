# tests for volcengine-tts speaker catalog helpers
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_SCRIPTS = Path(__file__).parent
_MODULE_PATH = _SCRIPTS / "volcengine-tts.py"
spec = importlib.util.spec_from_file_location("volcengine_tts", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_query_speakers_filter_scene():
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "视频配音", "heat": 50},
        {"voice_type": "b", "name": "B", "type": "bigtts", "scene": "通用场景", "heat": 100},
        {"voice_type": "c", "name": "C", "type": "icl", "scene": "视频配音", "heat": 80},
    ]
    result = mod.query_speakers(speakers, filters={"scene": "视频配音"}, sort_by="heat")
    assert len(result) == 2
    assert result[0]["name"] == "C"


def test_query_speakers_filter_type():
    speakers = [
        {"voice_type": "a", "name": "A", "type": "bigtts", "scene": "通用场景", "heat": 50},
        {"voice_type": "b", "name": "B", "type": "icl", "scene": "通用场景", "heat": 100},
    ]
    result = mod.query_speakers(speakers, filters={"type": "icl"}, sort_by=None)
    assert len(result) == 1
    assert result[0]["type"] == "icl"


def test_query_speakers_filter_lang():
    speakers = [
        {"voice_type": "a", "name": "A", "languages": ["zh-cn", "ja"], "heat": 1},
        {"voice_type": "b", "name": "B", "languages": ["en"], "heat": 2},
    ]
    result = mod.query_speakers(speakers, filters={"lang": "ja"}, sort_by=None)
    assert [s["name"] for s in result] == ["A"]


def test_query_speakers_no_filter():
    speakers = [{"voice_type": "a", "name": "A", "type": "bigtts", "scene": "s", "heat": 1}]
    result = mod.query_speakers(speakers, filters=None, sort_by=None)
    assert len(result) == 1


def test_parse_speaker_filters():
    assert mod.parse_speaker_filters(None) == {}
    assert mod.parse_speaker_filters(["scene=教学场景", "type=bigtts"]) == {
        "scene": "教学场景",
        "type": "bigtts",
    }


def test_parse_speaker_filters_rejects_bare_key(capsys):
    try:
        mod.parse_speaker_filters(["bigtts"])
    except SystemExit as e:
        assert e.code == 1
        err = capsys.readouterr().err
        assert "invalid --filter" in err
    else:
        raise AssertionError("expected SystemExit")


def test_catalog_contains_default_and_previous_builtin_ids():
    speakers = mod.load_speakers()
    ids = {s["voice_type"] for s in speakers}
    assert len(speakers) >= 400
    assert mod.DEFAULT_SPEAKER in ids
    assert "zh_male_m191_uranus_bigtts" in ids
    assert "en_female_dacey_uranus_bigtts" in ids
    types = {s["type"] for s in speakers}
    assert "bigtts" in types
    assert "icl" in types


def test_format_speaker_list_truncates_description():
    speakers = [{
        "name": "Vivi 2.0",
        "voice_type": "zh_female_vv_uranus_bigtts",
        "type": "bigtts",
        "gender": "女",
        "scene": "通用场景",
        "description": "x" * 80,
        "heat": 100,
    }]
    out = mod.format_speaker_list(speakers)
    assert out[0]["description"] == "x" * 40
    assert set(out[0]) == {
        "name", "voice_type", "type", "gender", "scene", "description", "heat",
    }


def test_list_speakers_cli_no_api_key():
    """--list-speakers must work without VOLC_SPEECH_API_KEY."""
    env = {k: v for k, v in os.environ.items() if k != "VOLC_SPEECH_API_KEY"}
    env.pop("VOLC_SPEECH_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--list-speakers", "--filter", "type=bigtts", "--sort", "heat"],
        cwd=str(_SCRIPTS.parent),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total"] > 0
    assert data["speakers"][0]["type"] == "bigtts"
    heats = [s["heat"] for s in data["speakers"]]
    assert heats == sorted(heats, reverse=True)
    assert "VOLC_SPEECH_API_KEY not found" not in result.stderr


def test_list_speakers_prints_total_wrapper(capsys):
    args = SimpleNamespace(filter=["scene=教学场景"], sort=None)
    mod._list_speakers(args)
    data = json.loads(capsys.readouterr().out)
    assert "total" in data
    assert "speakers" in data
    assert data["total"] == len(data["speakers"])
    assert all(s["scene"] == "教学场景" for s in data["speakers"])
