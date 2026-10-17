#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
"""Unit tests for deepseek_search.py (no network)."""

import argparse
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("deepseek_search", Path(__file__).with_name("deepseek_search.py"))
search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(search)


def search_args(**overrides):
    values = dict(query="Python 3.14", count=10, lang=None, after=None, before=None,
                  localization=None, ori_question=None, site=None, drop_localized=False,
                  exclude_domains=[], dedupe_domain=False, sort="rank", official_only=False,
                  timeout=45, retries=2, content_preview=500)
    values.update(overrides)
    return argparse.Namespace(**values)


class QueryTests(unittest.TestCase):
    def test_plain_query_is_trimmed(self):
        self.assertEqual(search.build_query(search_args(query="  hello  ")), "hello")

    def test_site_filters_join_with_or(self):
        args = search_args(site=["https://github.com/", "huggingface.co"])
        self.assertEqual(search.build_query(args), "Python 3.14 site:github.com OR site:huggingface.co")

    def test_all_filters_appended_in_order(self):
        args = search_args(lang="en", after="2025", before="2026-06-01", site=["arxiv.org"])
        self.assertEqual(
            search.build_query(args),
            "Python 3.14 site:arxiv.org lang:en after:2025 before:2026-06-01",
        )

    def test_query_over_limit_is_rejected(self):
        with self.assertRaises(SystemExit):
            search.validate_search_args(search_args(query="x" * 129))

    def test_site_filter_can_push_query_over_limit(self):
        with self.assertRaises(SystemExit):
            search.validate_search_args(search_args(query="x" * 120, site=["a" * 20]))

    def test_count_bounds(self):
        for count in (0, 51):
            with self.assertRaises(SystemExit):
                search.validate_search_args(search_args(count=count))
        self.assertEqual(search.validate_search_args(search_args(count=50)), "Python 3.14")

    def test_language_format(self):
        for lang in ("english", "EN", "zh-"):
            with self.assertRaises(SystemExit):
                search.validate_search_args(search_args(lang=lang))
        self.assertEqual(search.validate_search_args(search_args(lang="zh,en")), "Python 3.14 lang:zh,en")

    def test_date_format(self):
        for value in ("2026/10/01", "26-10", "2026-1-1"):
            with self.assertRaises(SystemExit):
                search.validate_search_args(search_args(after=value))

    def test_invalid_localization(self):
        with self.assertRaises(SystemExit):
            search.validate_search_args(search_args(localization="not-an-ip"))

    def test_normalize_site_strips_scheme_and_path(self):
        self.assertEqual(search.normalize_site("https://docs.python.org/3/"), "docs.python.org")


class MarkdownTests(unittest.TestCase):
    def test_unescape_headings_bullets_and_punctuation(self):
        raw = r"\#\# Summary \- item\. Next\, step\: ok"
        self.assertEqual(search.unescape_markdown(raw), "## Summary - item. Next, step: ok")

    def test_double_backslash_becomes_one(self):
        self.assertEqual(search.unescape_markdown(r"\\d+"), r"\d+")

    def test_escaped_dot_in_regex_is_preserved_after_double_escape(self):
        self.assertEqual(search.unescape_markdown(r"\\."), "\\.")

    def test_trailing_paragraph_anchor_removed(self):
        self.assertEqual(search.clean_markdown(r"\# Title¶"), "# Title")

    def test_boilerplate_removed(self):
        raw = r"Skip to main content" + "\n\n" + r"\# Spec" + "\n\nWas this page helpful?\n\nAssistant\n\nBody"
        cleaned = search.clean_markdown(raw)
        self.assertEqual(cleaned, "# Spec\n\nBody")

    def test_blank_line_collapse(self):
        self.assertEqual(search.clean_markdown("a\n\n\n\nb"), "a\n\nb")


class TruncateTests(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(search.truncate_text("abc", 10), ("abc", False))

    def test_zero_means_unlimited(self):
        self.assertEqual(search.truncate_text("abc", 0), ("abc", False))

    def test_truncates_at_line_boundary_with_marker(self):
        text = "line one\nline two\nline three"
        cut, truncated = search.truncate_text(text, 18)
        self.assertTrue(truncated)
        self.assertTrue(cut.startswith("line one\nline two"))
        self.assertIn("truncated", cut)
        self.assertLessEqual(len(cut), 18 + 80)

    def test_single_long_line_is_cut_hard(self):
        cut, truncated = search.truncate_text("x" * 100, 10)
        self.assertTrue(truncated)
        self.assertTrue(cut.startswith("x" * 10))


class FilterTests(unittest.TestCase):
    def rows(self):
        return [
            {"url": "https://docs.python.org/pl/3.15/whatsnew/3.14.html"},
            {"url": "https://docs.python.org/3/whatsnew/3.14.html"},
            {"url": "https://www.sohu.com/a/1"},
            {"url": "https://m.sohu.com/a/2"},
            {"url": "https://csdn.net/post/1"},
        ]

    def test_localized_mirror_host_is_detected(self):
        self.assertTrue(search.is_localized("https://python.github.io/python-docs-zh-tw/pr-preview/3.14.html"))
        self.assertFalse(search.is_localized("https://docs.python.org/3/whatsnew/3.14.html"))
        self.assertFalse(search.is_localized("https://docs.python.org/en/3/whatsnew/3.14.html"))

    def test_drop_localized_keeps_canonical_edition(self):
        kept, dropped = search.apply_result_filters(
            self.rows(), drop_localized=True, exclude_domains=[], dedupe_domain=False)
        self.assertEqual(dropped["localized"], 1)
        self.assertEqual(kept[0]["url"], "https://docs.python.org/3/whatsnew/3.14.html")

    def test_exclude_domains_ignores_www(self):
        kept, dropped = search.apply_result_filters(
            self.rows(), drop_localized=False, exclude_domains=["www.sohu.com"], dedupe_domain=False)
        self.assertEqual(dropped["excluded"], 2)
        self.assertFalse(any("sohu.com" in row["url"] for row in kept))

    def test_dedupe_domain_keeps_first(self):
        kept, dropped = search.apply_result_filters(
            self.rows(), drop_localized=False, exclude_domains=[], dedupe_domain=True)
        self.assertEqual(dropped["duplicate"], 2)
        self.assertEqual(len(kept), 3)


class OfficialSourceTests(unittest.TestCase):
    def test_government_education_and_igo_suffixes(self):
        for host in ("www.gov.cn", "miit.gov.cn", "mit.edu", "nju.edu.cn",
                     "ec.europa.eu", "who.int", "imf.org"):
            self.assertTrue(search.is_official_host(host), host)

    def test_curated_developer_domains(self):
        for host in ("docs.python.org", "github.com", "arxiv.org", "openai.com", "docs.vllm.ai"):
            self.assertTrue(search.is_official_host(host), host)

    def test_portals_and_ip_are_not_official(self):
        for host in ("tech.yahoo.com", "digit.in", "rootz.global", "219.237.218.35", "sohu.com"):
            self.assertFalse(search.is_official_host(host), host)

    def test_ip_detection(self):
        self.assertTrue(search.is_ip_host("219.237.218.35"))
        self.assertTrue(search.is_ip_host("[::1]"))
        self.assertFalse(search.is_ip_host("example.com"))

    def test_sort_official_is_stable(self):
        rows = [{"url": "https://a.com/1"}, {"url": "https://who.int/2"},
                {"url": "https://b.com/3"}, {"url": "https://github.com/4"}]
        ordered = search.sort_rows(rows, "official")
        self.assertEqual([row["url"] for row in ordered],
                         ["https://who.int/2", "https://github.com/4",
                          "https://a.com/1", "https://b.com/3"])

    def test_sort_rank_preserves_order(self):
        rows = [{"url": "https://a.com/1"}, {"url": "https://who.int/2"}]
        self.assertEqual(search.sort_rows(rows, "rank"), rows)

    def test_quality_warns_when_all_results_are_portals(self):
        quality = search.quality_summary([{"url": "https://tech.yahoo.com/a"},
                                          {"url": "https://digit.in/b"}])
        self.assertEqual(quality["official_count"], 0)
        self.assertIsNone(quality["official_first_rank"])
        self.assertIn("no official/primary domain", quality["warning"])

    def test_quality_reports_first_official_rank(self):
        quality = search.quality_summary([{"url": "https://a.com/1"},
                                          {"url": "https://b.com/2"},
                                          {"url": "https://c.com/3"},
                                          {"url": "https://who.int/4"}])
        self.assertEqual(quality["official_first_rank"], 4)
        self.assertFalse(quality["official_top3"])
        self.assertIn("rank 4", quality["warning"])

    def test_quality_flags_raw_ip(self):
        quality = search.quality_summary([{"url": "http://219.237.218.35/x"},
                                          {"url": "https://www.beijing.gov.cn/y"}])
        self.assertEqual(quality["ip_hosts"], ["219.237.218.35"])
        self.assertTrue(quality["official_top3"])
        self.assertIn("Raw IP", quality["warning"])

    def test_official_only_filter_reports_removed_rows(self):
        rows = [{"url": "https://tech.yahoo.com/a"}, {"url": "https://www.beijing.gov.cn/b"}]
        kept, dropped = search.apply_result_filters(
            rows, drop_localized=False, exclude_domains=[], dedupe_domain=False,
            official_only=True)
        self.assertEqual(len(kept), 1)
        self.assertEqual(dropped["not_official"], 1)

    def test_normalize_site_lowercases(self):
        self.assertEqual(search.normalize_site("GitHub.COM"), "github.com")


class OutputTests(unittest.TestCase):
    def test_error_message_prefers_nested_message(self):
        body = {"error": {"message": "bad request", "type": "invalid_request_error"}}
        self.assertEqual(search.error_message(body), "bad request")

    def test_error_message_handles_plain_text(self):
        self.assertEqual(search.error_message({"error": "boom"}), "boom")

    def test_human_output_contains_rank_url_meta(self):
        body = {"results": [{
            "title": "Docs", "url": "https://example.com/a", "site_name": "Example",
            "date": "2026-10-16T00:00:00+00:00", "authority": 4, "rerank_score": 2.41,
            "summary": "A summary.", "content": "",
        }]}
        text = search.format_search_human(body, "q", 120, 100)
        self.assertIn("1. Docs", text)
        self.assertIn("https://example.com/a", text)
        self.assertIn("auth 4", text)
        self.assertIn("rel 2.41", text)
        self.assertIn("2026-10-16", text)

    def test_human_output_handles_no_results(self):
        self.assertIn("No results", search.format_search_human({"results": []}, "q", 80, 100))

    def test_json_output_wraps_api_response(self):
        payload = json.loads(search.format_search_json({"results": []}, "q", 80, 1))
        self.assertEqual(payload["endpoint"], "/v1/tools/search")
        self.assertEqual(payload["api_response"], {"results": []})
        self.assertEqual(payload["query"], "q")

    def test_fetch_json_reports_fidelity_loss(self):
        payload = json.loads(search.format_fetch_json("T", "# T\n", "https://e.com", 10, 1, False, False))
        self.assertTrue(payload["notes"])
        self.assertEqual(payload["chars"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
