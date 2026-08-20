import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from image_engine import pixabay_client
from image_engine.image_candidate_collector import (
    ImageCandidateCollector
)
from image_engine.pixabay_client import (
    PixabayClient,
    PixabayCooldownError
)


class FakeResponse:

    def __init__(
        self,
        status_code=200,
        content=b"image"
    ):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return {"hits": []}


class PixabayCooldownTests(unittest.TestCase):

    def test_429_starts_cooldown(self):
        now = [100.0]
        calls = []

        def request_get(url, **kwargs):
            calls.append(url)
            if len(calls) == 1:
                return FakeResponse(status_code=429)
            return FakeResponse()

        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)

            with (
                patch.dict(
                    os.environ,
                    {"PIXABAY_API_KEY": "test-key"}
                ),
                patch.object(
                    pixabay_client.requests,
                    "get",
                    side_effect=request_get
                ),
                patch.object(
                    pixabay_client.time,
                    "monotonic",
                    side_effect=lambda: now[0]
                )
            ):
                client = PixabayClient()

                with self.assertRaises(PixabayCooldownError):
                    client.download_image(
                        "https://example.test/one.jpg",
                        folder / "one.jpg"
                    )

                with self.assertRaises(PixabayCooldownError):
                    client.download_image(
                        "https://example.test/two.jpg",
                        folder / "two.jpg"
                    )

                self.assertEqual(
                    calls,
                    ["https://example.test/one.jpg"]
                )

                now[0] += 60
                client.download_image(
                    "https://example.test/three.jpg",
                    folder / "three.jpg"
                )

                self.assertEqual(len(calls), 2)

    def test_collector_stops_pixabay_batch(self):
        class PexelsClientStub:
            def __init__(self):
                self.download_calls = 0

            def search(self, query, per_page):
                return ["pexels-one"]

            def download_image(self, image_url, save_path):
                self.download_calls += 1
                Path(save_path).write_bytes(b"image")

        class PixabayClientStub:
            def __init__(self):
                self.download_calls = 0

            def search(self, query, per_page, **kwargs):
                return ["one", "two", "three"]

            def download_image(self, image_url, save_path):
                self.download_calls += 1
                raise PixabayCooldownError(60)

        pexels = PexelsClientStub()
        pixabay = PixabayClientStub()
        collector = ImageCandidateCollector(
            pexels_client=pexels,
            pixabay_client=pixabay
        )

        with tempfile.TemporaryDirectory() as folder:
            output = io.StringIO()

            with redirect_stdout(output):
                candidates = collector.collect(
                    query="test",
                    image_folder=Path(folder),
                    attempt=1
                )

        self.assertEqual(len(candidates), 1)
        self.assertIn("pexels", candidates[0].name)
        self.assertEqual(pexels.download_calls, 1)
        self.assertEqual(pixabay.download_calls, 1)
        self.assertIn(
            "skipping remaining Pixabay",
            output.getvalue()
        )


if __name__ == "__main__":
    unittest.main()
