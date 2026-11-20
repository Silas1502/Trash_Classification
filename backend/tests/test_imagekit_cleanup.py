import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch, AsyncMock

import httpx
from imagekitio import ImageKit

from app.db.imagekit_cleanup import process_next_cleanup
from app.db.imagekit_storage import ImageKitStorage


ID = "00000000-0000-4000-8000-000000000001"
BASE = "https://ik.imagekit.io/test"
PATHS = [
    f"/uploads/single/2026/11/18/{ID}_ảnh thử.jpg",
    f"/uploads/xai/2026/11/18/{ID}_gradcam_overlay.jpg",
    f"/uploads/xai/2026/11/18/{ID}_spatial_energy_overlay.jpg",
]


class ImageDeletionTests(unittest.TestCase):
    def make_storage(self, handler):
        storage = ImageKitStorage.__new__(ImageKitStorage)
        storage.url_endpoint = BASE
        storage.client = ImageKit(private_key="private_testing", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(storage.close)
        return storage

    def test_resolves_three_legacy_urls_and_is_idempotent(self):
        files = {str(i): path for i, path in enumerate(PATHS)}
        deletions = []

        def handle(request):
            if request.method == "GET":
                # Deliberately include a similarly named unrelated image in every result.
                assets = [{"fileId": "unrelated", "filePath": PATHS[0] + ".copy", "type": "file"}]
                assets += [{"fileId": i, "filePath": p, "type": "file"} for i, p in files.items()]
                return httpx.Response(200, json=assets)
            file_id = request.url.path.rsplit("/", 1)[1]
            deletions.append(file_id)
            files.pop(file_id)
            return httpx.Response(204)

        storage = self.make_storage(handle)
        urls = [BASE + path.replace(" ", "%20") for path in PATHS]
        storage.delete_prediction_images(ID, urls + urls)
        storage.delete_prediction_images(ID, urls)
        self.assertCountEqual(deletions, ["0", "1", "2"])
        self.assertEqual(files, {})

    def test_deletes_new_folder_images_and_legacy_batch_images(self):
        new_names = ("original_ảnh thử.jpg", "gradcam_overlay.jpg", "spatial_energy_overlay.jpg")
        for folder in ("plastic", "paper", "metal", "glass", "manual", "batch"):
            with self.subTest(folder=folder):
                names = new_names if folder != "batch" else ("ảnh thử.jpg",)
                paths = [f"/uploads/{folder}/2026/11/18/{ID}_{name}" for name in names]
                files = {str(index): path for index, path in enumerate(paths)}
                assets = [{"fileId": file_id, "filePath": path, "type": "file"} for file_id, path in files.items()]
                deletions = []

                def handle(request):
                    if request.method == "GET":
                        self.assertEqual(request.url.params["path"], f"/uploads/{folder}/2026/11/18/")
                        return httpx.Response(200, json=assets)
                    deletions.append(request.url.path.rsplit("/", 1)[1])
                    return httpx.Response(204)

                self.make_storage(handle).delete_prediction_images(ID, [BASE + path for path in paths])
                self.assertCountEqual(deletions, files)

    def test_validates_all_urls_before_any_network_or_delete(self):
        called = Mock(side_effect=AssertionError("Must not touch ImageKit"))
        storage = self.make_storage(called)
        invalid = [
            "https://evil.example" + PATHS[0],
            BASE + PATHS[0].replace(ID, "00000000-0000-4000-8000-000000000002"),
            BASE + PATHS[0].replace("/single/", "/other/"),
            BASE + PATHS[0].replace("_ảnh thử.jpg", "_%2Fother.jpg"),
            BASE + PATHS[1].replace("_gradcam_overlay.jpg", "_unrelated.jpg"),
            BASE + PATHS[1].replace("/xai/", "/manual/").replace("_gradcam_overlay.jpg", "_unrelated.jpg"),
        ]
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                storage.delete_prediction_images(ID, [BASE + PATHS[0], url])
        called.assert_not_called()

    def test_delete_404_is_success(self):
        def handle(request):
            if request.method == "GET":
                return httpx.Response(200, json=[{"fileId": "f", "filePath": PATHS[0], "type": "file"}])
            return httpx.Response(404, json={"message": "already removed"})
        self.make_storage(handle).delete_prediction_images(ID, [BASE + PATHS[0]])

    def test_provider_error_is_not_misreported_as_already_deleted(self):
        from imagekitio import InternalServerError
        requests = []
        def handle(request):
            requests.append(request.method)
            return httpx.Response(500, json={"message": "provider unavailable"})
        storage = self.make_storage(handle)
        with self.assertRaises(InternalServerError):
            storage.delete_prediction_images(ID, [BASE + PATHS[0]])
        self.assertEqual(requests, ["GET"])  # No eager retry or deletion after failed lookup.

    def test_folder_lookup_paginates(self):
        skips = []
        def handle(request):
            if request.method == "DELETE":
                return httpx.Response(204)
            skip = int(request.url.params["skip"])
            skips.append(skip)
            if skip == 0:
                return httpx.Response(200, json=[{"fileId": str(i), "filePath": "/unrelated", "type": "file"} for i in range(100)])
            return httpx.Response(200, json=[{"fileId": "target", "filePath": PATHS[0], "type": "file"}])
        self.make_storage(handle).delete_prediction_images(ID, [BASE + PATHS[0]])
        self.assertEqual(skips, [0, 100])


class WorkerTests(unittest.TestCase):
    def test_empty_queue_does_not_touch_storage(self):
        history, storage = Mock(), Mock()
        history.client.rpc.return_value.execute.return_value.data = []
        self.assertFalse(process_next_cleanup(history, storage, "token"))
        storage.delete_prediction_images.assert_not_called()

    def test_acknowledges_success_and_requeues_failure_without_leaking_secrets(self):
        for failure in (None, RuntimeError("private key and URL must not leak")):
            with self.subTest(failure=failure):
                history, storage = Mock(), Mock()
                history.client.rpc.return_value.execute.return_value = SimpleNamespace(data=[{
                    "id": 7, "prediction_id": ID, "image_urls": [BASE + PATHS[0]], "lease_token": ID,
                }])
                storage.delete_prediction_images.side_effect = failure
                self.assertTrue(process_next_cleanup(history, storage, "token"))
                history.client.rpc.assert_called_with("imagekit_cleanup_finish", {
                    "p_token": "token", "p_id": 7, "p_lease": ID,
                    "p_error": "RuntimeError" if failure else None,
                })

    def test_storage_success_but_ack_failure_propagates_for_lease_retry(self):
        history, storage = Mock(), Mock()
        claim = Mock()
        claim.execute.return_value.data = [{"id": 7, "prediction_id": ID, "image_urls": [], "lease_token": ID}]
        finish = Mock()
        finish.execute.side_effect = ConnectionError("database unavailable")
        history.client.rpc.side_effect = [claim, finish]
        with self.assertRaises(ConnectionError):
            process_next_cleanup(history, storage, "token")


class LifespanTests(unittest.TestCase):
    def test_worker_starts_with_configuration_and_stops_on_shutdown(self):
        import asyncio
        from app.core.config import Settings
        from app.main import create_app
        from app.ml.types import DummyPredictor

        lifecycle = []
        async def worker(*args):
            lifecycle.append("started")
            try:
                await asyncio.Event().wait()
            finally:
                lifecycle.append("stopped")

        history = Mock()
        history.check = AsyncMock()
        settings = Settings(
            _env_file=None, supabase_url="https://testing.supabase.co", supabase_key="not-real",
            imagekit_private_key="not-real", imagekit_url_endpoint=BASE, imagekit_cleanup_token="x" * 64,
        )
        with patch("app.main.SupabaseHistory", return_value=history), patch.object(ImageKitStorage, "check"), patch("app.main.watch_imagekit_cleanup", worker):
            app = create_app(settings, model=DummyPredictor(("plastic", "paper", "metal", "glass")),
                batch_classifier=lambda *args: [], preprocessor_factory=lambda *args: object())
            async def exercise():
                async with app.router.lifespan_context(app):
                    await asyncio.sleep(0)
                    self.assertEqual(app.state.health["model"], "mock")
                    self.assertEqual(lifecycle, ["started"])
            asyncio.run(exercise())
            self.assertEqual(lifecycle, ["started", "stopped"])


if __name__ == "__main__":
    unittest.main()
