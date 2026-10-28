import base64
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import bot


SLUG = "financepress-2642867ae9784eae7919f62e"
JPEG = b"\xff\xd8\xff" + b"fake-jpeg-for-network-mock"
BUNDLE = {"topic": "Investasi", "sources": [], "post": {
    "title": "Memahami risiko investasi", "excerpt": "Risiko dan tujuan investasi.",
    "content": "<p>Isi artikel lama yang sudah disetujui.</p>",
    "slug": SLUG, "status": "draft", "categories": [814816]}}
MEDIA = {"id": 99, "source_url": "https://allaboutmoney.id/uploads/cover.jpg"}


def image_response():
    response = Mock(status_code=200)
    response.json.return_value = {"data": [{"b64_json": base64.b64encode(JPEG).decode()}],
                                  "usage": {"input_tokens": 50, "output_tokens": 196}}
    return response


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.bundle_path = self.data / (SLUG + ".json")
        self.bundle_path.write_text(json.dumps(BUNDLE))
        (self.root / "config.json").write_text('{"feeds": [], "keywords": []}')
        env = patch.dict(bot.os.environ, {"ENABLE_AI_IMAGE": "true", "POST_STATUS": "draft",
            "WP_URL": "https://allaboutmoney.id", "OPENAI_API_KEY": "fake-key-for-test",
            "INLINE_IMAGE": "true", "IMAGE_MODEL": "gpt-image-2.5-flare",
            "IMAGE_QUALITY": "low", "IMAGE_SIZE": "1536x1024"})
        env.start()
        self.addCleanup(env.stop)
        root = patch.object(bot, "ROOT", self.root)
        root.start()
        self.addCleanup(root.stop)
        metadata = patch.object(bot, "ensure_metadata", side_effect=lambda bundle, *_:
                                bundle.update(tag_names=["Investasi", "Saham", "Risiko"]))
        metadata.start()
        self.addCleanup(metadata.stop)
        tags = patch.object(bot, "resolve_tags", return_value=[])
        tags.start()
        self.addCleanup(tags.stop)
        self.auth = patch.object(bot, "check_auth")
        self.auth.start()
        self.addCleanup(self.auth.stop)

    def test_generate_once_then_reuse_local_image(self):
        bundle = copy.deepcopy(BUNDLE)
        with patch.object(bot.requests, "post", return_value=image_response()) as post:
            first = bot.generate_cover(bundle, self.data)
            second = bot.generate_cover(bundle, self.data)
            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), JPEG)
            post.assert_called_once()
            args = post.call_args.kwargs["json"]
            self.assertEqual(args["n"], 1)
            self.assertEqual(args["quality"], "low")
            self.assertEqual(args["output_format"], "jpeg")

    def test_dry_run_reuses_article_no_wordpress_write(self):
        with patch.object(bot.requests, "post", return_value=image_response()), \
             patch.object(bot, "ai", side_effect=AssertionError("Text AI must not run")), \
             patch.object(bot, "sync_site", side_effect=AssertionError("No RSS/site sync")), \
             patch.object(bot, "wp_request") as wp:
            bot.run(True, "data/" + self.bundle_path.name)
            wp.assert_not_called()
        preview = self.bundle_path.with_suffix(".html").read_text()
        self.assertIn(SLUG + "-cover.jpg", preview)
        self.assertIn(BUNDLE["post"]["content"], preview)

    def test_upload_cached_cover_sets_featured_media_and_inline(self):
        (self.data / (SLUG + "-cover.jpg")).write_bytes(JPEG)
        with patch.object(bot.requests, "post", side_effect=AssertionError("No paid regeneration")), \
             patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[], [], MEDIA, {"id": 42, "status": "draft"}]
            bot.run(False, "data/" + self.bundle_path.name)
            payload = wp.call_args_list[-1].kwargs["json"]
            self.assertEqual(payload["featured_media"], 99)
            self.assertIn(MEDIA["source_url"], payload["content"])
            self.assertIn(BUNDLE["post"]["content"], payload["content"])
            self.assertEqual(payload["status"], "publish")
            self.assertEqual(wp.call_args_list[2].args, ("POST", "media"))
        saved = json.loads(self.bundle_path.read_text())
        self.assertEqual(saved["image"]["media_id"], 99)
        self.assertEqual(saved["post"]["content"], BUNDLE["post"]["content"])

    def test_existing_featured_media_does_not_generate_or_upload(self):
        with patch.object(bot, "generate_cover") as generate, patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[{"id": 42, "status": "publish", "featured_media": 88}],
                              {"id": 42, "status": "publish"}]
            bot.run(False, "data/" + self.bundle_path.name)
            generate.assert_not_called()
            self.assertEqual(wp.call_count, 2)

    def test_from_preview_publishes_reviewed_text_over_existing_draft(self):
        (self.data / (SLUG + "-cover.jpg")).write_bytes(JPEG)
        with patch.object(bot, "wp_request") as wp:
            wp.side_effect = [[{"id": 42, "status": "publish", "featured_media": 0,
                                "content": {"raw": "<p>Versi edit redaksi</p>"}}],
                              [MEDIA], {"id": 42, "status": "publish"}]
            bot.run(False, "data/" + self.bundle_path.name)
            update = wp.call_args.kwargs["json"]
            self.assertEqual(update["status"], "publish")
            self.assertNotIn("Versi edit redaksi", update["content"])
            self.assertIn("Isi artikel lama", update["content"])
            self.assertEqual(wp.call_args.args, ("POST", "posts/42"))

    def test_image_failure_blocks_post_and_saves_article(self):
        response = Mock(status_code=403)
        response.json.return_value = {"error": {"code": "model_not_found", "message": "fake-key-for-test"}}
        with patch.object(bot.requests, "post", return_value=response), patch.object(bot, "wp_request", return_value=[]) as wp:
            with self.assertRaisesRegex(RuntimeError, "model_not_found") as error:
                bot.run(False, "data/" + self.bundle_path.name)
            self.assertNotIn("fake-key-for-test", str(error.exception))
            wp.assert_called_once()
            self.assertEqual(wp.call_args.args[0], "GET")
        self.assertTrue(self.bundle_path.is_file())
        self.assertFalse((self.data / (SLUG + "-cover.jpg")).exists())

    def test_recover_media_upload_by_slug(self):
        path = self.data / (SLUG + "-cover.jpg")
        path.write_bytes(JPEG)
        with patch.object(bot, "wp_request", return_value=[MEDIA]) as wp:
            result = bot.upload_cover(copy.deepcopy(BUNDLE), path, self.bundle_path)
            self.assertEqual(result["id"], 99)
            wp.assert_called_once()
            self.assertEqual(wp.call_args.kwargs["params"]["slug"], SLUG + "-cover")

    def test_bad_base64_is_not_saved(self):
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"b64_json": "!invalid!"}]}
        with patch.object(bot.requests, "post", return_value=response):
            with self.assertRaises(RuntimeError):
                bot.generate_cover(copy.deepcopy(BUNDLE), self.data)
        self.assertFalse((self.data / (SLUG + "-cover.jpg")).exists())

    def test_wp_credentials_normalized(self):
        with patch.dict(bot.os.environ, {"WP_USERNAME": " vibemamah ", "WP_APP_PASSWORD": "abcd efgh ijkl"}), \
             patch.object(bot.requests, "request") as request:
            request.return_value.status_code = 200
            request.return_value.json.return_value = {}
            bot.wp_request("GET", "users/me")
            self.assertEqual(request.call_args.kwargs["auth"], ("vibemamah", "abcdefghijkl"))

    def test_upload_permission_required(self):
        self.auth.stop()
        with patch.object(bot, "wp_request", return_value={"capabilities": {"edit_posts": True}}):
            with self.assertRaisesRegex(RuntimeError, "upload_files"):
                bot.check_auth()

    def test_cross_site_preview_rejected(self):
        bundle = copy.deepcopy(BUNDLE)
        bundle["site_url"] = "https://other.example"
        self.bundle_path.write_text(json.dumps(bundle))
        with patch.object(bot, "wp_request") as wp:
            with self.assertRaisesRegex(RuntimeError, "situs berbeda"):
                bot.run(False, "data/" + self.bundle_path.name)
            wp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
