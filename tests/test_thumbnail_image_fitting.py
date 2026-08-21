import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from thumbnail_engine.thumbnail_generator import (
    ThumbnailGenerator
)
from thumbnail_engine.thumbnail_pptx_generator import (
    ThumbnailPptxGenerator
)


class ThumbnailImageFittingTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.placeholder = SimpleNamespace(
            left=100,
            top=200,
            width=300,
            height=200
        )
        self.generator = ThumbnailPptxGenerator()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _image(self, name, size, mode="RGB", color="red"):
        path = self.directory / name
        Image.new(mode, size, color).save(path)
        return path

    def _prepare(self, path):
        return self.generator._prepare_image(
            image_path=path,
            placeholder=self.placeholder
        )

    def test_landscape_image_fits_entirely_without_cropping(self):
        source = self._image("landscape.jpg", (600, 200))

        _, left, top, width, height = self._prepare(source)

        self.assertEqual((left, top, width, height), (100, 250, 300, 100))

    def test_portrait_image_fits_entirely_without_cropping(self):
        source = self._image("portrait.jpg", (100, 400))

        _, left, top, width, height = self._prepare(source)

        self.assertEqual((left, top, width, height), (225, 200, 50, 200))

    def test_aspect_ratio_is_preserved(self):
        source = self._image("ratio.jpg", (640, 360))

        _, _, _, width, height = self._prepare(source)

        self.assertAlmostEqual(width / height, 640 / 360, places=2)
        self.assertLessEqual(width, self.placeholder.width)
        self.assertLessEqual(height, self.placeholder.height)

    def test_transparent_png_preserves_alpha(self):
        source = self._image(
            "transparent.png",
            (40, 40),
            mode="RGBA",
            color=(255, 0, 0, 80)
        )

        prepared, *_ = self._prepare(source)

        self.assertEqual(prepared, source)
        with Image.open(prepared) as image:
            self.assertIn("A", image.getbands())
            self.assertEqual(image.getchannel("A").getextrema(), (80, 80))

    def test_transparent_webp_conversion_preserves_alpha(self):
        source = self._image(
            "transparent.webp",
            (40, 40),
            mode="RGBA",
            color=(255, 0, 0, 80)
        )

        prepared, *_ = self._prepare(source)

        self.assertEqual(prepared.suffix, ".png")
        self.assertTrue(source.is_file())
        with Image.open(prepared) as image:
            self.assertIn("A", image.getbands())
            alpha_min, alpha_max = image.getchannel("A").getextrema()
            self.assertLess(alpha_min, 255)
            self.assertLess(alpha_max, 255)

    def test_ordinary_jpeg_remains_valid(self):
        source = self._image("ordinary.jpg", (320, 240))

        prepared, *_ = self._prepare(source)

        self.assertEqual(prepared, source)
        with Image.open(prepared) as image:
            self.assertEqual(image.format, "JPEG")

    def test_transparent_pixels_show_template_background_not_black(self):
        source = self._image(
            "overlay.png",
            (20, 20),
            mode="RGBA",
            color=(0, 0, 0, 0)
        )
        canvas = Image.new("RGB", (60, 60), (20, 40, 60))

        ThumbnailGenerator()._paste_image(
            canvas,
            source,
            (10, 10, 50, 50)
        )

        self.assertEqual(canvas.getpixel((30, 30)), (20, 40, 60))


if __name__ == "__main__":
    unittest.main()
