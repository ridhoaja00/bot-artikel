import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import bot


ARTICLE = {"title": "Contoh", "excerpt": "Ringkasan", "sections": [
    {"heading": "Konteks", "paragraphs": [{"text": "Teks <script> berbahaya", "source_ids": [1, 2]}]}]}
SOURCES = [{"title": "Satu", "url": "https://a.example/news", "published": "2026-10-28"},
           {"title": "Dua", "url": "https://b.example/news", "published": "2026-10-28"}]


class Tests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(bot.os.environ, {"ENABLE_AI_IMAGE": "false", "POST_STATUS": "draft"})
        env.start()
        self.addCleanup(env.stop)
        metadata = patch.object(bot, "ensure_metadata", side_effect=lambda bundle, *_:
                                bundle.update(tag_names=["Investasi", "Saham", "Risiko"]))
        metadata.start()
        self.addCleanup(metadata.stop)
        tags = patch.object(bot, "resolve_tags", return_value=[])
        tags.start()
        self.addCleanup(tags.stop)
        enrich = patch.object(bot, "enrich_sources", side_effect=lambda sources: sources)
        enrich.start()
        self.addCleanup(enrich.stop)
        relevance = patch.object(bot, "relevant_sources", side_effect=lambda topic, sources: sources)
        relevance.start()
        self.addCleanup(relevance.stop)

    def test_maps_existing_category_id(self):
        self.assertEqual(bot.category_ids({"category_slug": "crypto"},
            {"category_slugs": ["crypto"]},
            {"categories": [{"id": 814818, "slug": "crypto"}]}), [814818])

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValueError):
            bot.category_ids({"category_slug": "invented"},
                             {"category_slugs": ["crypto"]}, {"categories": []})

    def test_sync_reads_public_data_and_excludes_default_post(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bot, "ROOT", Path(folder)), \
             patch.object(bot, "public_get") as get:
            get.side_effect = [{"name": "All About Money", "timezone_string": "Asia/Jakarta"},
                [{"id": 814818, "slug": "crypto", "name": "Crypto"}],
                [{"slug": "hello-world"}, {"slug": "bitcoin", "title": {"rendered": "Bitcoin"},
                  "link": "https://allaboutmoney.id/bitcoin/", "categories": [814818],
                  "excerpt": {"rendered": "<p>Risiko pasar</p>"}}]]
            profile = bot.sync_site({"category_slugs": ["crypto"]})
            self.assertEqual(len(profile["recent_posts"]), 1)
            self.assertEqual(profile["categories"][0]["id"], 814818)
            self.assertTrue((Path(folder) / "site-profile.json").exists())

    def test_sync_missing_category_stops(self):
        with patch.object(bot, "public_get", side_effect=[{"name": "Site"}, []]):
            with self.assertRaises(ValueError):
                bot.sync_site({"category_slugs": ["crypto"]})

    def test_check_auth_has_no_write(self):
        with patch.object(bot, "wp_request", return_value={"capabilities": {"edit_posts": True}}) as wp, \
             patch.dict(bot.os.environ, {"POST_STATUS": "draft"}):
            bot.check_auth()
            self.assertEqual(wp.call_args.args, ("GET", "users/me"))

    def test_cannot_publish_without_permission(self):
        with patch.object(bot, "wp_request", return_value={"capabilities": {"edit_posts": True}}), \
             patch.dict(bot.os.environ, {"POST_STATUS": "publish"}):
            with self.assertRaises(ValueError):
                bot.check_auth()

    def test_invalid_reference_rejected(self):
        with self.assertRaises(ValueError):
            bot.validate_article(ARTICLE, 1)

    def test_untrusted_html_escaped(self):
        result = bot.render(ARTICLE, SOURCES)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def flow(self, root, dry=False, existing=False):
        (root / "config.json").write_text(json.dumps({"feeds": [], "keywords": []}))
        with patch.object(bot, "ROOT", root), patch.object(bot, "fetch_sources", return_value=SOURCES), \
             patch.object(bot, "choose", return_value=("Topik", SOURCES)), \
             patch.object(bot, "write_article", return_value=ARTICLE), \
             patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[{"id": 4, "status": "draft", "content": {"rendered": '<a href="https://a.example/news">Sumber</a>'}}]] if existing else [[], {"id": 4, "status": "draft"}]
            bot.run(dry)
            return wp.call_args_list

    def test_dry_run_never_uploads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(self.flow(root, dry=True), [])
            self.assertEqual(len(list((root / "data").glob("*.html"))), 1)

    def test_success_deduplicated_next_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(len(self.flow(root)), 2)
            self.assertEqual(self.flow(root), [])

    def test_reconcile_existing_post(self):
        with tempfile.TemporaryDirectory() as folder:
            calls = self.flow(Path(folder), existing=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].args[0], "GET")


if __name__ == "__main__":
    unittest.main()
