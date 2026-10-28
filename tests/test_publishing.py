import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot

SLUG = "financepress-2642867ae9784eae7919f62e"
BUNDLE = {"topic": "Investasi", "tag_names": ["Saham", "Investasi", "Risiko"], "post": {
    "title": "Memahami risiko saham", "excerpt": "Memahami tujuan dan risiko investasi saham.",
    "content": "<p>Isi artikel yang diperiksa.</p>", "slug": SLUG,
    "categories": [814816], "status": "draft"}}
PROFILE = {"categories": [{"id": 814816, "slug": "investasi", "name": "Investasi"}]}
CONFIG = {"category_slugs": ["investasi"]}


class PublishingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "data").mkdir()
        self.path = self.root / "data" / (SLUG + ".json")
        self.path.write_text(json.dumps(BUNDLE))
        (self.root / "config.json").write_text(json.dumps(CONFIG))
        env = patch.dict(bot.os.environ, {"POST_STATUS": "draft", "ENABLE_AI_IMAGE": "false",
                                         "WP_URL": "https://allaboutmoney.id"})
        env.start()
        self.addCleanup(env.stop)
        root = patch.object(bot, "ROOT", self.root)
        root.start()
        self.addCleanup(root.stop)

    def test_legacy_metadata_completed_without_rewriting_text(self):
        bundle = copy.deepcopy(BUNDLE)
        bundle.pop("tag_names")
        bundle["post"]["categories"] = [123]
        bundle["post"]["excerpt"] = ""
        with patch.object(bot, "ai", return_value={"category_slug": "investasi",
            "tag_names": ["Saham", "Risiko", "Investasi"], "excerpt": "Ringkasan baru."}) as ai:
            bot.ensure_metadata(bundle, CONFIG, PROFILE)
            ai.assert_called_once()
        self.assertEqual(bundle["post"]["title"], BUNDLE["post"]["title"])
        self.assertEqual(bundle["post"]["content"], BUNDLE["post"]["content"])
        self.assertEqual(bundle["post"]["categories"], [814816])
        self.assertEqual(bundle["category_names"], ["Investasi"])
        self.assertEqual(len(bundle["tag_names"]), 3)

    def test_prepared_metadata_does_not_call_ai(self):
        bundle = copy.deepcopy(BUNDLE)
        with patch.object(bot, "ai", side_effect=AssertionError("No paid AI call")):
            bot.ensure_metadata(bundle, CONFIG, PROFILE)
        self.assertEqual(bundle["category_names"], ["Investasi"])

    def test_preview_displays_all_metadata_without_remote_writes(self):
        with patch.object(bot, "sync_site", return_value=PROFILE), \
             patch.object(bot, "ai", side_effect=AssertionError("No paid text regeneration")), \
             patch.object(bot, "wp_request") as wp:
            bot.run(True, self.path)
            wp.assert_not_called()
        html = self.path.with_suffix(".html").read_text()
        for text in ["Investasi", "Saham", "Risiko", "langsung publik", BUNDLE["post"]["excerpt"]]:
            self.assertIn(text, html)

    def test_publish_uses_saved_payload_and_ignores_old_draft_setting(self):
        with patch.object(bot, "sync_site", return_value=PROFILE), \
             patch.object(bot, "resolve_tags", return_value=[11, 12, 13]), \
             patch.object(bot, "wp_request") as wp, \
             patch.object(bot, "ai", side_effect=AssertionError("No paid text call")):
            wp.side_effect = [{"capabilities": {"edit_posts": True, "publish_posts": True}},
                              [], {"id": 55, "status": "publish", "link": "https://allaboutmoney.id/example/"}]
            bot.run(False, self.path)
            payload = wp.call_args.kwargs["json"]
            self.assertEqual(payload["status"], "publish")
            self.assertEqual(payload["title"], BUNDLE["post"]["title"])
            self.assertEqual(payload["content"], BUNDLE["post"]["content"])
            self.assertEqual(payload["categories"], [814816])
            self.assertEqual(payload["tags"], [11, 12, 13])
            self.assertEqual(payload["excerpt"], BUNDLE["post"]["excerpt"])
        saved = json.loads(self.path.read_text())
        self.assertEqual(saved["wordpress"]["status"], "publish")
        self.assertIn("published_signature", saved)

    def test_existing_draft_is_published_in_place(self):
        with patch.object(bot, "sync_site", return_value=PROFILE), \
             patch.object(bot, "resolve_tags", return_value=[11, 12, 13]), \
             patch.object(bot, "wp_request") as wp:
            wp.side_effect = [{"capabilities": {"edit_posts": True, "publish_posts": True}},
                [{"id": 55, "status": "draft", "featured_media": 0}], {"id": 55, "status": "publish"}]
            bot.run(False, self.path)
            self.assertEqual(wp.call_args.args, ("POST", "posts/55"))
            self.assertEqual(wp.call_args.kwargs["json"]["status"], "publish")

    def test_repeat_command_does_not_publish_again(self):
        bundle = copy.deepcopy(BUNDLE)
        bundle["wordpress"] = {"post_id": 55, "status": "publish"}
        bundle["published_signature"] = bot.preview_signature(bundle)
        self.path.write_text(json.dumps(bundle))
        with patch.object(bot, "sync_site", return_value=PROFILE), \
             patch.object(bot, "resolve_tags") as tags, \
             patch.object(bot, "wp_request") as wp:
            wp.side_effect = [{"capabilities": {"edit_posts": True, "publish_posts": True}},
                              [{"id": 55, "status": "publish"}]]
            bot.run(False, self.path)
            self.assertEqual(wp.call_count, 2)
            tags.assert_not_called()

    def test_publish_permission_checked_before_tag_or_post_writes(self):
        with patch.object(bot, "sync_site", return_value=PROFILE), \
             patch.object(bot, "wp_request", return_value={"capabilities": {"edit_posts": True}}) as wp, \
             patch.object(bot, "resolve_tags") as tags:
            with self.assertRaisesRegex(ValueError, "publish_posts"):
                bot.run(False, self.path)
            wp.assert_called_once()
            tags.assert_not_called()

    def test_existing_and_new_tags_are_resolved_by_slug(self):
        with patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[{"id": 11}], [], {"id": 12}, [{"id": 13}]]
            self.assertEqual(bot.resolve_tags(["Saham", "Investasi", "Risiko"]), [11, 12, 13])
            self.assertEqual(wp.call_args_list[2].args, ("POST", "tags"))
            self.assertEqual(wp.call_args_list[2].kwargs["json"], {"name": "Investasi", "slug": "investasi"})

    def test_tag_timeout_recovered_without_duplicate_creation(self):
        with patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[], RuntimeError("timeout"), [{"id": 11}], [{"id": 12}], [{"id": 13}]]
            self.assertEqual(bot.resolve_tags(["Saham", "Investasi", "Risiko"]), [11, 12, 13])
            self.assertEqual(sum(c.args[0] == "POST" for c in wp.call_args_list), 1)

    def test_tags_cannot_be_empty_or_duplicate_only(self):
        with self.assertRaises(RuntimeError):
            bot.clean_tags(["Saham", "saham", "SAHAM"])


if __name__ == "__main__":
    unittest.main()
