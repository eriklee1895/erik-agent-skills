"""Offline checks for official Seedance 2.5 reference contracts."""
from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (SKILL_DIR / relative_path).read_text(encoding="utf-8")


class ReferenceContract(unittest.TestCase):
    def test_1080p_bit_depth_is_not_mislabeled_as_universal_hevc(self):
        matrix = read("references/seedance-2.5.md")
        self.assertNotIn("10-bit HEVC", read("SKILL.md") + matrix)
        self.assertIn("1080p（10-bit）", matrix)

    def test_edit_duration_documents_source_tolerance(self):
        api = read("references/api-reference.md")
        self.assertIn("基本一致", api)
        self.assertIn("0.4 秒", api)

    def test_generate_audio_does_not_invent_stereo_contract(self):
        docs = "".join(read(path) for path in (
            "SKILL.md", "references/api-reference.md", "references/key-constraints.md",
        ))
        self.assertNotIn("双声道", docs)

    def test_model_activation_prerequisite_is_linked(self):
        self.assertIn("seedance-model-activation-usage-and-refund", read("SKILL.md"))

    def test_current_family_rate_limits_are_retrievable(self):
        constraints = read("references/key-constraints.md")
        for expected in ("企业", "600", "个人", "180", "20 QPS", "任务列表1 QPS", "取消或删除20 QPS"):
            self.assertIn(expected, constraints)

    def test_auto_multimodal_recommendation_is_explicit(self):
        matrix = read("references/seedance-2.5.md")
        self.assertIn("不区分子任务", matrix)
        self.assertIn("推荐", matrix)

    def test_official_sound_markers_are_not_misattributed(self):
        guide = read("references/prompt-guide.md")
        self.assertIn("官方系列教程推荐", guide)
        self.assertIn("音乐用 `()`", guide)

    def test_cookbook_has_no_retired_generation_wording(self):
        self.assertNotIn("两代", read("references/scene-cookbook.md"))

    def test_quickstart_reference_prompts_use_at_mentions(self):
        skill = read("SKILL.md")
        self.assertIn("@音频1", skill)
        self.assertIn("@视频1", skill)

    def test_task_list_filter_requires_endpoint_id(self):
        api = read("references/api-reference.md")
        self.assertIn("`ep-...`", api)
        self.assertNotIn("精确模型名", api)

    def test_cancelled_task_retention_is_24_hours(self):
        self.assertRegex(read("references/api-reference.md"), r"cancelled.{0,20}24\s*小时")

    def test_last_frame_url_validity_is_explicit(self):
        self.assertRegex(read("references/api-reference.md"), r"last_frame_url.{0,100}24\s*小时")

    def test_files_expiry_cursor_and_delete_contracts_are_retrievable(self):
        files = read("references/files-api.md")
        for expected in ("默认7天", "`last_id`", "`has_more`", "不可逆"):
            self.assertIn(expected, files)

    def test_tos_source_and_destination_storage_are_distinct(self):
        files = read("references/files-api.md")
        self.assertIn("目标存储", files)
        self.assertIn("可选", files)

    def test_cookbook_examples_avoid_internal_contradictions(self):
        cookbook = read("references/scene-cookbook.md")
        self.assertNotIn("白衣剑客；黑衣剑客。全程同一人", cookbook)
        self.assertNotIn("暖金早晨", cookbook)

    def test_hard_cut_is_conditional_not_mandatory_syntax(self):
        cookbook = read("references/scene-cookbook.md")
        self.assertNotIn("多镜加 `Hard cut.`", cookbook)
        self.assertNotIn("2.5 多镜用硬切分开", cookbook)

    def test_extension_boundary_action_is_recommendation(self):
        self.assertNotIn("prompt 必须写", read("references/scene-cookbook.md"))

    def test_reference_guide_covers_order_scope_and_ratio_routing(self):
        guide = read("references/prompt-guide.md")
        for expected in ("首次出场顺序", "不要复制", "需要改宽高比"):
            self.assertIn(expected, guide)

    def test_subtitle_troubleshooting_covers_reference_video(self):
        self.assertIn("参考图和视频", read("references/prompt-guide.md"))

    def test_white_model_guidance_covers_fine_models(self):
        self.assertIn("精细白模", read("references/prompt-guide.md"))

    def test_sound_marker_provenance_is_consistent_in_summary(self):
        self.assertIn("官方推荐", read("SKILL.md"))

    def test_files_list_limit_range_is_preserved(self):
        self.assertIn("1–100", read("references/files-api.md"))


if __name__ == "__main__":
    unittest.main()
