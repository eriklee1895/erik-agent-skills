# skills/volcengine-asr/scripts/test_volcengine_asr.py
"""Offline tests for volcengine-asr subtitle/normalization logic (no API calls)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module("volcengine_asr_transcribe", _SCRIPTS_DIR / "transcribe.py")
subtitle = _load_module("volcengine_asr_subtitle", _SCRIPTS_DIR / "subtitle.py")
for _name in dir(subtitle):
    if not _name.startswith("__") and not hasattr(mod, _name):
        setattr(mod, _name, getattr(subtitle, _name))


# ── timestamps ─────────────────────────────────────────────────────────────

def test_srt_timestamp_format():
    assert mod.fmt_srt_timestamp(0) == "00:00:00,000"
    assert mod.fmt_srt_timestamp(61_234) == "00:01:01,234"
    assert mod.fmt_srt_timestamp(3_723_456) == "01:02:03,456"


def test_vtt_timestamp_uses_dot():
    assert mod.fmt_vtt_timestamp(61_234) == "00:01:01.234"
    assert mod.fmt_vtt_timestamp(-5) == "00:00:00.000"


# ── request body ───────────────────────────────────────────────────────────

def test_build_request_body_minimal():
    body = mod.build_request_body(audio_data_b64="abc")
    assert body["audio"]["data"] == "abc"
    assert "user" not in body
    req = body["request"]
    assert req["model_name"] == "bigmodel"
    assert req["show_utterances"] is True
    assert req["enable_ddc"] is False
    assert "enable_speaker_info" not in req


def test_build_request_body_diarize_and_meeting():
    body = mod.build_request_body(audio_url="https://x/a.mp3", audio_format="mp3", diarize=True)
    assert body["audio"]["url"] == "https://x/a.mp3"
    assert body["audio"]["format"] == "mp3"
    assert body["request"]["enable_speaker_info"] is True
    assert body["request"]["ssd_version"] == "200"

    body2 = mod.build_request_body(audio_url="https://x/a.mp3", meeting=True)
    assert body2["request"]["ssd_version"] == "300"


def test_build_request_body_language_and_hotwords():
    body = mod.build_request_body(audio_data_b64="x", language="zh-CN", hotwords=["豆包", "火山引擎"])
    assert body["audio"]["language"] == "zh-CN"
    ctx = json.loads(body["request"]["corpus"]["context"])
    words = [h["word"] for h in ctx["hotwords"]]
    assert words == ["豆包", "火山引擎"]


def test_build_request_body_data_mode_includes_format():
    # The standard 2.0 request always identifies the uploaded audio format.
    body = mod.build_request_body(audio_data_b64="x", audio_format="mp3")
    assert body["audio"]["format"] == "mp3"


def test_build_request_body_serializes_full_context_payload():
    context = {
        "context_type": "dialog_ctx",
        "context_data": [{"speaker": "user", "text": "这是上一轮对话"}],
        "hotwords": [{"word": "奥德赛"}],
    }
    body = mod.build_request_body(audio_data_b64="x", audio_format="mp3", context=context)
    assert json.loads(body["request"]["corpus"]["context"]) == context


def test_context_hotwords_merge_with_cli_hotwords_without_duplicates():
    context = {
        "context_type": "dialog_ctx",
        "hotwords": [{"word": "奥德赛"}, {"word": "荷马"}],
    }
    body = mod.build_request_body(
        audio_data_b64="x",
        audio_format="mp3",
        context=context,
        hotwords=["荷马", "诺兰"],
    )
    payload = json.loads(body["request"]["corpus"]["context"])
    assert payload["context_type"] == "dialog_ctx"
    assert [item["word"] for item in payload["hotwords"]] == ["奥德赛", "荷马", "诺兰"]


def test_load_context_json_reads_and_validates_provider_object(tmp_path):
    path = tmp_path / "context.json"
    expected = {
        "context_type": "dialog_ctx",
        "context_data": [{"speaker": "user", "text": "领域背景"}],
    }
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    assert mod.load_context_json(path) == expected


def test_build_request_body_standard_data_mode_includes_format():
    # Standard submit requires explicit format even for base64 data upload.
    body = mod.build_request_body(audio_data_b64="x", audio_format="mp3", send_format=True)
    assert body["audio"]["format"] == "mp3"
    assert body["audio"]["data"] == "x"


class _FakeResponse:
    def __init__(self, *, code="20000000", payload=None, http_status=200, message="OK"):
        self.status_code = http_status
        self.headers = {
            "X-Api-Status-Code": code,
            "X-Api-Message": message,
            "X-Tt-Logid": "log-1",
        }
        self._payload = payload or {}
        self.content = json.dumps(self._payload).encode()
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload


def test_standard_queries_with_task_id_returned_by_submit(monkeypatch):
    """The current API returns a server task_id that may differ from request UUID."""
    calls = []
    responses = iter([
        _FakeResponse(payload={"task_id": "server-task-id"}),
        _FakeResponse(payload={"audio_info": {"duration": 1}, "result": {"text": "好"}}),
    ])

    def fake_post(url, headers, body, *, timeout):
        calls.append((url, headers.copy(), body, timeout))
        return next(responses)

    monkeypatch.setattr(mod, "_post", fake_post)
    result = mod.recognize_standard(
        api_key="key",
        audio_url="https://example.com/audio.mp3",
        audio_format="mp3",
        poll_interval=0,
        timeout_s=1,
    )

    assert result["text"] == "好"
    assert calls[1][1]["X-Api-Request-Id"] == "server-task-id"
    assert "X-Api-Sequence" not in calls[1][1]


def test_standard_falls_back_to_request_id_for_legacy_data_upload(monkeypatch, tmp_path):
    """Legacy base64 submit may return an empty body and echo the query id in a header."""
    calls = []
    responses = iter([
        _FakeResponse(payload={}),
        _FakeResponse(payload={"audio_info": {"duration": 1}, "result": {"text": "好"}}),
    ])

    def fake_post(url, headers, body, *, timeout):
        calls.append((url, headers.copy(), body, timeout))
        return next(responses)

    audio_path = tmp_path / "compat.mp3"
    audio_path.write_bytes(b"audio")
    monkeypatch.setattr(mod, "_post", fake_post)
    result = mod.recognize_standard(
        api_key="key",
        audio_path=audio_path,
        audio_format="mp3",
        poll_interval=0,
        timeout_s=1,
    )

    assert result["text"] == "好"
    assert calls[1][1]["X-Api-Request-Id"] == calls[0][1]["X-Api-Request-Id"]


def test_documented_url_submit_without_task_id_fails_closed(monkeypatch):
    calls = []

    def fake_post(url, headers, body, *, timeout):
        calls.append((url, headers.copy(), body, timeout))
        return _FakeResponse(payload={})

    monkeypatch.setattr(mod, "_post", fake_post)
    result = mod.recognize_standard(
        api_key="key",
        audio_url="https://example.com/audio.mp3",
        audio_format="mp3",
        poll_interval=0,
        timeout_s=1,
    )

    assert "without task_id" in result["error"]
    assert len(calls) == 1


def test_standard_query_auth_error_stops_without_polling_to_timeout(monkeypatch):
    responses = iter([
        _FakeResponse(payload={"task_id": "server-task-id"}),
        _FakeResponse(http_status=401, code="", message="unauthorized"),
    ])
    monkeypatch.setattr(mod, "_post", lambda *args, **kwargs: next(responses))
    result = mod.recognize_standard(
        api_key="bad-key",
        audio_url="https://example.com/audio.mp3",
        audio_format="mp3",
        poll_interval=0,
        timeout_s=30,
    )
    assert result["error"] == "query authentication failed: HTTP 401"


def test_standard_rejects_audio_over_five_hours_before_upload(monkeypatch, tmp_path):
    audio = tmp_path / "long.mp3"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(mod, "probe_duration_s", lambda path: 5 * 3600 + 1)
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr(mod, "_post", fail_if_called)
    result = mod.recognize_standard(
        api_key="key", audio_path=audio, audio_format="mp3"
    )
    assert "above the 5h standard limit" in result["error"]
    assert called is False


def test_public_cli_exposes_only_standard_model():
    script = Path(__file__).parent / "volcengine-asr.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "--mode" not in proc.stdout
    assert "volc.seedasr.auc" in proc.stdout
    assert "--context-json" in proc.stdout


def test_subtitle_cli_rejects_valid_json_with_invalid_transcript_shape(tmp_path):
    transcript_path = tmp_path / "invalid.transcript.json"
    transcript_path.write_text("[]", encoding="utf-8")
    script = Path(__file__).parent / "subtitle.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(transcript_path), "--srt"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 1
    error = json.loads(proc.stderr)
    assert "object" in error["error"]


def test_subtitle_cli_rejects_invalid_nested_utterance_shape(tmp_path):
    transcript_path = tmp_path / "invalid-nested.transcript.json"
    transcript_path.write_text(
        json.dumps({"utterances": [None], "speakers": []}), encoding="utf-8"
    )
    script = Path(__file__).parent / "subtitle.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(transcript_path), "--srt"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 1
    error = json.loads(proc.stderr)
    assert "utterances" in error["error"]


def test_subtitle_cli_rerenders_saved_transcript_without_asr(tmp_path):
    transcript_path = tmp_path / "saved.transcript.json"
    transcript_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "text": "你好。",
                "duration_ms": 800,
                "utterances": [
                    {
                        "text": "你好。",
                        "start_ms": 0,
                        "end_ms": 800,
                        "speaker": None,
                        "channel": None,
                        "words": [
                            {"text": "你", "start_ms": 0, "end_ms": 300},
                            {"text": "好。", "start_ms": 300, "end_ms": 800},
                        ],
                    }
                ],
                "speakers": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "rerendered.srt"
    script = Path(__file__).parent / "subtitle.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(transcript_path), "--srt", str(output_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    assert "00:00:00,000 --> 00:00:00,800" in output_path.read_text(encoding="utf-8")
    assert "你好。" in output_path.read_text(encoding="utf-8")


def test_transcript_only_writes_word_timestamps_without_subtitles(tmp_path):
    meta_path = tmp_path / "narration.meta.json"
    meta_path.write_text(
        json.dumps(
            {
                "sentence_text": "你好",
                "words": [
                    {"word": "你", "startTime": 0.0, "endTime": 0.3},
                    {"word": "好", "startTime": 0.3, "endTime": 0.6},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    script = Path(__file__).parent / "volcengine-asr.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--from-tts-meta",
            str(meta_path),
            "--transcript-only",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    transcript_path = tmp_path / "narration.transcript.json"
    assert transcript_path.exists()
    assert not (tmp_path / "narration.srt").exists()
    assert not (tmp_path / "narration.vtt").exists()
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    assert transcript["utterances"][0]["words"][0] == {
        "text": "你",
        "start_ms": 0,
        "end_ms": 300,
        "confidence": 0,
    }
    assert transcript["mode"] == "tts-meta"
    assert "cues" in transcript


def test_prepare_local_media_converts_ffmpeg_failure_to_json_exit(monkeypatch, tmp_path, capsys):
    audio = tmp_path / "broken.m4a"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(mod, "standard_limit_reason", lambda path: None)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(mod, "ffmpeg_to_mp3", lambda source, destination: (_ for _ in ()).throw(RuntimeError("bad media")))

    with pytest.raises(SystemExit) as exc:
        mod.prepare_local_media(audio)

    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().err)["error"] == "bad media"


def test_keep_extracted_failure_preserves_existing_output(monkeypatch, tmp_path, capsys):
    audio = tmp_path / "broken.m4a"
    audio.write_bytes(b"audio")
    existing = tmp_path / "broken.asr-16k-mono.mp3"
    existing.write_bytes(b"previous-good-output")
    monkeypatch.setattr(mod, "standard_limit_reason", lambda path: None)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(
        mod,
        "ffmpeg_to_mp3",
        lambda source, destination: (_ for _ in ()).throw(RuntimeError("bad media")),
    )

    with pytest.raises(SystemExit):
        mod.prepare_local_media(audio, keep_extracted=True)

    assert existing.read_bytes() == b"previous-good-output"
    assert json.loads(capsys.readouterr().err)["error"] == "bad media"


def test_raw_audio_extension_is_accepted():
    assert ".raw" in mod.AUDIO_EXTS


def test_raw_ffmpeg_command_declares_headerless_pcm_input():
    cmd = mod.build_ffmpeg_cmd(Path("in.raw"), Path("out.mp3"))
    assert cmd.index("-f") < cmd.index("-i")
    assert cmd[cmd.index("-f") + 1] == "s16le"
    assert cmd[cmd.index("-ar") + 1] == "16000"
    assert cmd[cmd.index("-ac") + 1] == "1"


# ── ffmpeg extraction ──────────────────────────────────────────────────────

def test_ffmpeg_cmd_preserves_pts_timeline():
    # Regression: sources with PTS gaps (recording pauses, concatenated clips)
    # produced cumulatively drifting subtitles until extraction honored PTS.
    cmd = mod.build_ffmpeg_cmd(Path("in.mp4"), Path("out.mp3"))
    assert "-af" in cmd
    af = cmd[cmd.index("-af") + 1]
    assert "aresample=async=1:first_pts=0" in af
    assert cmd[0] == "ffmpeg" and "-vn" in cmd


# ── normalization ──────────────────────────────────────────────────────────

def test_normalize_result_parses_utterances_and_speakers():
    raw = {
        "audio_info": {"duration": 6312},
        "result": {
            "text": "你好。世界。",
            "utterances": [
                {
                    "start_time": 0, "end_time": 2000, "text": "你好。",
                    "additions": {"speaker": "1"},
                    "words": [
                        {"text": "你", "start_time": 0, "end_time": 1000, "confidence": 0.9},
                        {"text": "好", "start_time": 1000, "end_time": 2000, "confidence": 0.8},
                    ],
                },
                {
                    "start_time": 2000, "end_time": 4000, "text": "世界。",
                    "additions": {"speaker": "2"},
                    "words": [
                        {"text": "世", "start_time": 2000, "end_time": 3000, "confidence": 0.7},
                        {"text": "界", "start_time": 3000, "end_time": 4000, "confidence": 0.6},
                    ],
                },
            ],
        },
    }
    out = mod.normalize_result(raw, log_id="L1")
    assert out["duration_ms"] == 6312
    assert out["text"] == "你好。世界。"
    assert out["speakers"] == ["1", "2"]
    assert out["utterances"][0]["words"][0] == {
        "text": "你",
        "start_ms": 0,
        "end_ms": 1000,
        "confidence": 0.9,
        "blank_duration_ms": 0,
    }
    assert out["log_id"] == "L1"


def test_normalize_result_duration_from_additions():
    raw = {"result": {"additions": {"duration": "1234"}, "utterances": []}}
    assert mod.normalize_result(raw)["duration_ms"] == 1234


def test_speaker_label_map_first_appearance():
    labels = mod.speaker_label_map(["2", "0", "1"])
    assert labels == {"2": "A", "0": "B", "1": "C"}


# ── cue grouping ───────────────────────────────────────────────────────────

def w(text, start, end, speaker=None):
    return {"text": text, "start_ms": start, "end_ms": end, "speaker": speaker}


def test_words_to_cues_sentence_punctuation_breaks():
    words = [w("你", 0, 500), w("好", 500, 1000), w("。", 1000, 1100),
             w("世", 2000, 2500), w("界", 2500, 3000), w("。", 3000, 3100)]
    cues = mod.words_to_cues(words)
    assert len(cues) == 2
    assert cues[0]["text"] == "你好。"
    assert cues[1]["text"] == "世界。"
    assert cues[0]["start_ms"] == 0 and cues[0]["end_ms"] == 1100
    assert cues[1]["start_ms"] == 2000


def test_words_to_cues_speaker_change_flushes():
    words = [w("你", 0, 500, "1"), w("好", 500, 1000, "1"),
             w("嗨", 1100, 1600, "2"), w("呀", 1600, 2100, "2")]
    cues = mod.words_to_cues(words)
    assert len(cues) == 2
    assert cues[0]["speaker"] == "1" and cues[0]["text"] == "你好"
    assert cues[1]["speaker"] == "2" and cues[1]["text"] == "嗨呀"


def test_words_to_cues_silence_gap_flushes():
    words = [w("第一句", 0, 1000), w("第二句", 3000, 4000)]  # 2s gap
    cues = mod.words_to_cues(words)
    assert len(cues) == 2
    assert cues[1]["start_ms"] == 3000


def test_words_to_cues_hard_char_cap_forces_break():
    # No punctuation anywhere; must still break at the hard cap (~30 weighted).
    words = [w("字", i * 300, i * 300 + 300) for i in range(40)]
    cues = mod.words_to_cues(words, max_weight=20, max_duration_ms=10_000)
    assert len(cues) >= 2
    assert all(mod.text_weight(c["text"]) <= 20 * mod.HARD_CUE_FACTOR + 1 for c in cues)


def test_words_to_cues_clause_punct_needs_min_length():
    # Short clause early on should NOT split; long-enough clause should.
    short = [w("好", 0, 200), w("，", 200, 300), w("我", 400, 600), w("们", 600, 800),
             w("继", 800, 1000), w("续", 1000, 1200), w("。", 1200, 1300)]
    cues = mod.words_to_cues(short)
    assert len(cues) == 1  # "好，我们继续。" stays together

    long = [w("字", i * 200, i * 200 + 200) for i in range(12)] + [w("，", 2400, 2500)] + \
           [w("后", 2600, 2800), w("半", 2800, 3000), w("句", 3000, 3200)]
    cues = mod.words_to_cues(long)
    assert len(cues) == 2
    assert cues[1]["text"] == "后半句"


def test_words_to_cues_latin_spacing():
    words = [w("Hello", 0, 500), w("world", 500, 1000), w("!", 1000, 1100)]
    cues = mod.words_to_cues(words)
    assert cues[0]["text"] == "Hello world!"


def test_words_to_cues_no_spurious_space_around_cjk_punct():
    words = [w("Hello", 0, 500), w("，", 500, 600), w("world", 700, 1200)]
    cues = mod.words_to_cues(words)
    assert cues[0]["text"] == "Hello，world"


def test_cue_end_never_before_start_plus_minimum():
    words = [w("嗯", 1000, 1000)]  # zero-duration token
    cues = mod.words_to_cues(words)
    assert cues[0]["end_ms"] >= cues[0]["start_ms"] + 200


# ── proportional fallback (utterances without word timestamps) ─────────────

def test_proportional_words_fallback():
    utts = [{
        "text": "你好，世界。",
        "start_ms": 0, "end_ms": 4000,
        "speaker": "1", "words": [],
    }]
    words = mod.utterances_to_proportional_words(utts)
    texts = [x["text"] for x in words]
    assert "你好，" in texts and "世界。" in texts
    assert words[0]["start_ms"] == 0
    assert words[-1]["end_ms"] == 4000


# ── rendering ──────────────────────────────────────────────────────────────

def test_render_srt_structure_and_speaker_prefix():
    cues = [
        {"start_ms": 0, "end_ms": 2000, "text": "你好。", "speaker": "1"},
        {"start_ms": 2000, "end_ms": 4000, "text": "世界。", "speaker": "2"},
    ]
    srt = mod.render_srt(cues, {"1": "A", "2": "B"})
    lines = srt.splitlines()
    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:02,000"
    assert lines[2] == "【发言人A】你好。"
    assert "【发言人B】世界。" in srt
    assert lines[4] == "2"


def test_render_vtt_header_and_dot_timestamp():
    cues = [{"start_ms": 0, "end_ms": 1500, "text": "嗨", "speaker": None}]
    vtt = mod.render_vtt(cues, {})
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:01.500" in vtt
    assert "【发言人" not in vtt


def test_render_txt_speaker_prefix():
    utts = [
        {"text": "甲说的话", "speaker": "1"},
        {"text": "乙说的话", "speaker": "2"},
    ]
    txt = mod.render_txt(utts, {"1": "A", "2": "B"})
    assert "发言人A：甲说的话" in txt
    assert "发言人B：乙说的话" in txt


# ── TTS meta reuse ─────────────────────────────────────────────────────────

def test_load_tts_meta_converts_seconds_to_ms(tmp_path):
    meta = {
        "text": "你好世界",
        "sentence_text": "你好世界",
        "duration_ms": 1010,
        "words": [
            {"word": "你", "startTime": 0.22, "endTime": 0.33, "confidence": 0.9},
            {"word": "好", "startTime": 0.33, "endTime": 0.55, "confidence": 0.8},
        ],
    }
    p = tmp_path / "tts_001.meta.json"
    p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    out = mod.load_tts_meta(p)
    assert out["source"] == "tts-meta"
    w0 = out["utterances"][0]["words"][0]
    assert w0["start_ms"] == 220 and w0["end_ms"] == 330
    assert out["utterances"][0]["speaker"] is None


def test_tts_meta_end_to_end_srt(tmp_path):
    meta = {
        "sentence_text": "大家好，欢迎收听。",
        "words": [
            {"word": "大", "startTime": 0.0, "endTime": 0.3},
            {"word": "家", "startTime": 0.3, "endTime": 0.6},
            {"word": "好", "startTime": 0.6, "endTime": 0.9},
            {"word": "，", "startTime": 0.9, "endTime": 1.0},
            {"word": "欢", "startTime": 1.5, "endTime": 1.8},
            {"word": "迎", "startTime": 1.8, "endTime": 2.1},
            {"word": "收", "startTime": 2.1, "endTime": 2.4},
            {"word": "听", "startTime": 2.4, "endTime": 2.7},
            {"word": "。", "startTime": 2.7, "endTime": 2.8},
        ],
    }
    p = tmp_path / "tts_20260904_001.meta.json"
    p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    transcript = mod.load_tts_meta(p)
    words = mod.flatten_words(transcript["utterances"])
    cues = mod.words_to_cues(words)
    srt = mod.render_srt(cues, {})
    assert "大家好，" in srt
    assert "欢迎收听。" in srt
    assert "00:00:00,000" in srt


# ── punctuation re-insertion ───────────────────────────────────────────────

def test_reinsert_punctuation_chinese():
    words = [
        {"text": "你", "start_ms": 0, "end_ms": 100},
        {"text": "好", "start_ms": 100, "end_ms": 200},
        {"text": "世", "start_ms": 300, "end_ms": 400},
        {"text": "界", "start_ms": 400, "end_ms": 500},
    ]
    out = mod.reinsert_punctuation("你好，世界。", words)
    assert [w["text"] for w in out] == ["你", "好，", "世", "界。"]


def test_reinsert_punctuation_english():
    words = [
        {"text": "Hello", "start_ms": 0, "end_ms": 100},
        {"text": "world", "start_ms": 200, "end_ms": 300},
    ]
    out = mod.reinsert_punctuation("Hello, world!", words)
    assert [w["text"] for w in out] == ["Hello,", "world!"]


def test_reinsert_punctuation_missing_word_is_safe():
    words = [{"text": "你", "start_ms": 0, "end_ms": 1}]
    out = mod.reinsert_punctuation("完全不同的文本。", words)
    assert out[0]["text"] == "你"  # untouched on alignment failure


def test_normalize_result_reinserts_punctuation():
    raw = {
        "result": {
            "text": "你好，世界。",
            "utterances": [{
                "start_time": 0, "end_time": 500, "text": "你好，世界。",
                "additions": {"speaker": "1"},
                "words": [
                    {"text": "你", "start_time": 0, "end_time": 100},
                    {"text": "好", "start_time": 100, "end_time": 200},
                    {"text": "世", "start_time": 300, "end_time": 400},
                    {"text": "界", "start_time": 400, "end_time": 500},
                ],
            }],
        }
    }
    out = mod.normalize_result(raw)
    tokens = [w["text"] for w in out["utterances"][0]["words"]]
    assert tokens == ["你", "好，", "世", "界。"]


def test_english_space_tokens_dropped_and_spacing_rederived():
    # Live API (English) returns explicit space tokens with start/end = -1.
    raw = {"result": {"text": "Hello, world. This is a test.",
        "utterances": [
            {"start_time": 40, "end_time": 800, "text": "Hello, world.", "additions": {}, "words": [
                {"text": "Hello,", "start_time": 40, "end_time": 480},
                {"text": " ", "start_time": -1, "end_time": -1},
                {"text": "world.", "start_time": 600, "end_time": 800},
                {"text": " ", "start_time": -1, "end_time": -1},
            ]},
            {"start_time": 1080, "end_time": 1400, "text": "This is a test.", "additions": {}, "words": [
                {"text": "This", "start_time": 1080, "end_time": 1200},
                {"text": " ", "start_time": -1, "end_time": -1},
                {"text": "is", "start_time": 1200, "end_time": 1300},
                {"text": " ", "start_time": -1, "end_time": -1},
                {"text": "a", "start_time": 1300, "end_time": 1350},
                {"text": " ", "start_time": -1, "end_time": -1},
                {"text": "test.", "start_time": 1350, "end_time": 1400},
            ]},
        ]}}
    out = mod.normalize_result(raw)
    flat = mod.flatten_words(out["utterances"])
    assert all(t["text"].strip() for t in flat)
    assert all(t["start_ms"] >= 0 and t["end_ms"] >= 0 for t in flat)
    cues = mod.words_to_cues(flat)
    texts = [c["text"] for c in cues]
    assert texts == ["Hello, world.", "This is a test."]
    assert "  " not in " ".join(texts)
    assert cues[0]["start_ms"] == 40 and cues[0]["end_ms"] == 800


# ── hotwords ───────────────────────────────────────────────────────────────

def test_parse_hotwords_dedup_and_normalize():
    assert mod.parse_hotwords("豆包，火山引擎, 豆包,Seedance") == ["豆包", "火山引擎", "Seedance"]
    assert mod.parse_hotwords("") is None
    assert mod.parse_hotwords(None) is None
