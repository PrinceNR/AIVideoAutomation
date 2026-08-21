import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from thumbnail_engine.thumbnail_generator import ThumbnailGenerator
from thumbnail_engine.thumbnail_pptx_generator import ThumbnailPptxGenerator


class ThumbnailDefaultImageTests(unittest.TestCase):

    def _word(self, name, default_image):
        return SimpleNamespace(
            word=name,
            default_image=(
                str(default_image)
                if default_image is not None
                else None
            ),
        )

    def test_exact_default_image_is_chosen_instead_of_first_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            first_candidate = folder / "attempt_01.jpg"
            selected = folder / "attempt_03.jpg"
            first_candidate.touch()
            selected.touch()

            result = ThumbnailPptxGenerator()._find_word_image(
                self._word("hesitate", selected)
            )

            self.assertEqual(result, selected)
            self.assertNotEqual(result, first_candidate)

    def test_manual_override_path_is_honored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manual = Path(temp_dir) / "manual" / "override.webp"
            manual.parent.mkdir()
            manual.touch()

            result = ThumbnailGenerator()._find_word_image(
                self._word("curious", manual)
            )

            self.assertEqual(result, manual)

    def test_missing_or_invalid_default_does_not_pick_folder_candidate(self):
        generators = (
            ThumbnailPptxGenerator(),
            ThumbnailGenerator(),
        )

        for generator in generators:
            with self.subTest(generator=type(generator).__name__):
                with self.assertRaisesRegex(
                    FileNotFoundError,
                    "No default image is selected",
                ):
                    generator._find_word_image(
                        self._word("gather", None)
                    )

                with self.assertRaisesRegex(
                    FileNotFoundError,
                    "Selected thumbnail image not found",
                ):
                    generator._find_word_image(
                        self._word("gather", "missing.jpg")
                    )

    def test_existing_slot_ordering_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            template = folder / "template.png"
            output = folder / "thumbnail.png"
            Image.new("RGB", (1280, 720), "white").save(template)

            words = []
            for index, name in enumerate(("first", "second", "third")):
                image_path = folder / f"{index}.png"
                Image.new("RGB", (10, 10), "black").save(image_path)
                words.append(self._word(name, image_path))

            generator = ThumbnailGenerator()
            with patch.object(generator, "_paste_image") as paste_image:
                with patch.object(generator, "_draw_word") as draw_word:
                    generator.generate(
                        lesson=SimpleNamespace(words=words),
                        lesson_folder=folder,
                        output_path=output,
                        template_path=template,
                    )

            self.assertEqual(
                [call.args[1] for call in paste_image.call_args_list],
                [Path(word.default_image) for word in words],
            )
            self.assertEqual(
                [call.args[1] for call in draw_word.call_args_list],
                [word.word for word in words],
            )


if __name__ == "__main__":
    unittest.main()
