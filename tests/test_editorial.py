import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import bot


def paragraph(words=80):
    return {"text": " ".join("kata" + str(i) for i in range(words)), "source_ids": [1]}


def long_article():
    return {"title": "Demutualisasi BEI: Perubahan Kepemilikan dan Tata Kelola Bursa",
            "excerpt": "Konteks perubahan kepemilikan bursa dan risiko bagi investor.",
            "category_slug": "investasi", "tag_names": ["BEI", "Demutualisasi", "Pasar Modal"],
            "lead": [paragraph()], "key_points": [paragraph(20) for _ in range(3)],
            "closing": [paragraph()], "sections": [{"heading": "Bagian " + str(i),
                "paragraphs": [paragraph(), paragraph()]} for i in range(5)]}


class EditorialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "data").mkdir()
        env = patch.dict(bot.os.environ, {"ENABLE_AI_IMAGE": "false", "POST_STATUS": "draft",
            "WP_URL": "https://allaboutmoney.id", "ARTICLE_MIN_WORDS": "700", "ARTICLE_TARGET_WORDS": "1100"})
        env.start()
        self.addCleanup(env.stop)
        root = patch.object(bot, "ROOT", self.root)
        root.start()
        self.addCleanup(root.stop)

    def test_tracking_parameters_do_not_bypass_duplicate_filter(self):
        self.assertEqual(bot.canonical_url("https://www.example.com/news/?utm_source=rss&fbclid=x"),
                         bot.canonical_url("https://example.com/news"))

    def test_reservations_cover_published_sources_and_unpublished_previews(self):
        profile = {"recent_posts": [{"title": "Artikel terbit", "source_urls": ["https://a.example/news"], "categories": [1]}],
                   "categories": [{"id": 1, "slug": "crypto"}, {"id": 2, "slug": "bisnis"}]}
        bundle = {"post": {"title": "Preview baru", "categories": [1]},
                  "sources": [{"url": "https://b.example/news?utm_source=test"}]}
        (self.root / "data" / "preview.json").write_text(json.dumps(bundle))
        used, titles, priority = bot.reservation_state(profile, self.root / "data")
        self.assertEqual(len(used), 2)
        self.assertIn("Preview baru", titles)
        self.assertEqual(priority[0], "bisnis")

    def test_source_for_same_event_not_just_shared_institution(self):
        sources = [{"title": "BEI sepakat demutualisasi, anggaran dasar dirombak", "summary": "Bursa Efek Indonesia"},
                   {"title": "Transformasi BUMN dari 1074 jadi 200 perusahaan", "summary": "Danantara Indonesia"}]
        self.assertEqual(bot.relevant_sources("Demutualisasi Bursa Efek Indonesia", sources), sources[:1])

    def test_parser_prefers_article_body_and_skips_navigation(self):
        parser = bot.PublicArticleParser()
        parser.feed('<article><p>' + 'Pengantar tidak dipakai. ' * 4 + '</p><div class="detail-text">'
                    '<p>' + 'Fakta publik yang relevan. ' * 20 + '</p>'
                    '<nav><p>' + 'Promosi tidak dipakai. ' * 4 + '</p></nav></div></article>')
        text = parser.text()
        self.assertIn("Fakta publik", text)
        self.assertNotIn("Pengantar", text)
        self.assertNotIn("Promosi", text)

    def test_paywall_flag_is_not_bypassed(self):
        source = {"url": "https://source.example/news", "summary": "Cuplikan terbuka."}
        response = Mock(text='<script>{"isAccessibleForFree":false}</script><article><p>' + 'rahasia ' * 150 + '</p></article>')
        with patch.object(bot.requests, "get", return_value=response):
            result = bot.enrich_sources([source])
        self.assertNotIn("article_text", result[0])

    def test_long_article_accepted_and_counted(self):
        with patch.object(bot, "ai", return_value=long_article()) as ai:
            article = bot.write_article("Demutualisasi BEI", [{"article_text": "sumber " * 400}], {}, {})
        self.assertGreaterEqual(article["word_count"], 700)
        ai.assert_called_once()

    def test_short_article_is_repaired_once_not_silently_published(self):
        short = {"title": "Pendek", "sections": [{"heading": "Satu", "paragraphs": [paragraph(30)]}]}
        with patch.object(bot, "ai", return_value=short) as ai:
            with self.assertRaisesRegex(RuntimeError, "terlalu pendek"):
                bot.write_article("Topik", [{"article_text": "sumber " * 400}], {}, {})
            self.assertEqual(ai.call_count, 2)

    def test_insufficient_sources_stop_before_paid_writing(self):
        with patch.object(bot, "ai") as ai:
            with self.assertRaisesRegex(RuntimeError, "Bahan sumber terlalu sedikit"):
                bot.write_article("Topik", [{"summary": "hanya cuplikan"}], {}, {})
            ai.assert_not_called()

    def test_readable_slug_separate_from_legacy_file_key(self):
        old = {"post": {"slug": "financepress-6bfeb712ed3442f568cb24bb", "title": "Judul"}}
        self.assertEqual(bot.bundle_key(old), "6bfeb712ed3442f568cb24bb")
        slug = bot.pretty_slug("Demutualisasi BEI: Apa yang Berubah bagi Investor?")
        self.assertEqual(slug, "demutualisasi-bei-berubah-investor")
        self.assertNotIn("financepress", slug)

    def test_normal_new_post_does_not_reuse_published_source(self):
        config = {"feeds": [], "keywords": [], "category_slugs": ["bisnis"]}
        (self.root / "config.json").write_text(json.dumps(config))
        profile = {"categories": [{"id": 1, "slug": "bisnis", "name": "Bisnis"}],
            "recent_posts": [{"title": "Sudah terbit", "source_urls": ["https://source.example/news"], "categories": [1]}]}
        with patch.object(bot, "sync_site", return_value=profile), \
             patch.object(bot, "fetch_sources", return_value=[{"url": "https://source.example/news?utm_source=rss"}]), \
             patch.object(bot, "choose") as choose:
            bot.run(True)
            choose.assert_not_called()

    def test_semantic_title_variation_is_not_a_new_post(self):
        self.assertTrue(bot.similar_topic("Demutualisasi BEI dan Perubahan Kepemilikan Bursa",
                                         ["Perubahan Kepemilikan Bursa: Demutualisasi BEI"]))

    def test_choose_obeys_explicit_category(self):
        items = [{"url": "https://source.example/news", "title": "Pajak bisnis UMKM", "summary": "Pajak UMKM dan bisnis"}]
        config = {"category_slugs": ["bisnis", "crypto"], "_requested_category": "bisnis", "min_domains": 1}
        with patch.object(bot, "ai", return_value={"topic": "Pajak bisnis UMKM", "indices": [0], "category_slug": "bisnis"}) as ai:
            topic, sources = bot.choose(items, [], config)
            self.assertEqual(ai.call_args.args[1]["category_priority"], ["bisnis"])
            self.assertEqual(topic, "Pajak bisnis UMKM")
            self.assertEqual(sources, items)

    def test_revision_updates_known_post_id_after_slug_change(self):
        config = {"feeds": [], "keywords": []}
        (self.root / "config.json").write_text(json.dumps(config))
        key = "6bfeb712ed3442f568cb24bb"
        path = self.root / "data" / ("financepress-" + key + ".json")
        bundle = {"item_key": key, "site_url": bot.site_url(), "target_post_id": 50,
                  "tag_names": ["BEI", "Demutualisasi", "Bursa"], "post": {
                      "title": "Demutualisasi BEI untuk Investor", "slug": "demutualisasi-bei-investor",
                      "content": "<p>Isi revisi diperiksa.</p>", "excerpt": "Ringkasan revisi", "categories": [1]}}
        path.write_text(json.dumps(bundle))
        with patch.object(bot, "check_auth"), patch.object(bot, "resolve_tags", return_value=[11, 12, 13]), \
             patch.object(bot, "wp_request") as wp:
            wp.side_effect = [{"id": 50, "status": "publish", "featured_media": 0},
                              {"id": 50, "status": "publish", "link": "https://allaboutmoney.id/new/"}]
            bot.run(False, path)
            self.assertEqual(wp.call_args_list[0].args, ("GET", "posts/50"))
            self.assertEqual(wp.call_args_list[-1].args, ("POST", "posts/50"))
            self.assertEqual(wp.call_args.kwargs["json"]["slug"], "demutualisasi-bei-investor")

    def test_preparing_revision_keeps_target_and_cover(self):
        previous = {"item_key": "6bfeb712ed3442f568cb24bb", "target_post_id": 50,
            "post": {"slug": "financepress-6bfeb712ed3442f568cb24bb", "title": "Judul lama"},
            "image": {"media_id": 49, "source_url": "https://allaboutmoney.id/cover.jpg"}}
        sources = [{"url": "https://source.example/bei", "title": "Demutualisasi BEI", "summary": "Demutualisasi BEI"}]
        profile = {"categories": [{"id": 1, "slug": "investasi", "name": "Investasi"}], "recent_posts": []}
        config = {"category_slugs": ["investasi"]}
        with patch.object(bot, "enrich_sources", side_effect=lambda items: items), \
             patch.object(bot, "write_article", return_value=long_article()):
            bundle = bot.prepare_article("Demutualisasi BEI", sources, profile, config, previous)
        self.assertEqual(bundle["target_post_id"], 50)
        self.assertEqual(bundle["image"]["media_id"], 49)
        self.assertNotIn("financepress", bundle["post"]["slug"])
        self.assertIn(previous["post"]["slug"], bundle["lookup_slugs"])


if __name__ == "__main__":
    unittest.main()
