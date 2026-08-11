from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps


class ThumbnailGenerator:

    def __init__(self):
        # 1280 x 720 template
        # Each slot has:
        # - image_box = where the image should go
        # - text_box = where the word should be written
        self.slots = [
            {
                "image_box": (46, 191, 309, 331),
                "text_box": (33, 372, 322, 420),
            },
            {
                "image_box": (355, 191, 617, 331),
                "text_box": (342, 372, 631, 420),
            },
            {
                "image_box": (663, 191, 925, 331),
                "text_box": (650, 372, 939, 420),
            },
            {
                "image_box": (972, 191, 1234, 331),
                "text_box": (959, 372, 1248, 420),
            },
            {
                "image_box": (46, 460, 309, 598),
                "text_box": (33, 641, 322, 689),
            },
            {
                "image_box": (355, 460, 617, 598),
                "text_box": (342, 641, 631, 689),
            },
            {
                "image_box": (663, 460, 925, 598),
                "text_box": (650, 641, 939, 689),
            },
            {
                "image_box": (972, 460, 1234, 598),
                "text_box": (959, 641, 1248, 689),
            },
        ]

    def generate(
        self,
        lesson,
        lesson_folder,
        output_path,
        template_path,
    ):
        lesson_folder = Path(lesson_folder)
        output_path = Path(output_path)
        template_path = Path(template_path)

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}"
            )

        base = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(base)

        words = lesson.words[:8]

        for index, word in enumerate(words):
            slot = self.slots[index]

            image_path = self._find_word_image(
                lesson_folder,
                word.word
            )

            if image_path is not None:
                self._paste_image(
                    base,
                    image_path,
                    slot["image_box"]
                )
            else:
                print(
                    f"Image not found for word: {word.word}"
                )

            self._draw_word(
                draw,
                word.word,
                slot["text_box"]
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        base.save(output_path)

        print(f"Thumbnail created: {output_path}")

        return output_path

    def _find_word_image(
        self,
        lesson_folder,
        word_name
    ):
        word_folder = (
            lesson_folder
            / "images"
            / self._normalize_name(word_name)
        )

        if not word_folder.exists():
            return None

        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            files = sorted(word_folder.glob(pattern))
            if files:
                return files[0]

        return None

    def _paste_image(
        self,
        canvas,
        image_path,
        image_box
    ):
        left, top, right, bottom = image_box
        width = right - left
        height = bottom - top

        image = Image.open(image_path).convert("RGB")

        # Fit image nicely inside the slot
        fitted = ImageOps.fit(
            image,
            (width, height),
            method=Image.Resampling.LANCZOS
        )

        canvas.paste(fitted, (left, top))

    def _draw_word(
        self,
        draw,
        word,
        text_box
    ):
        left, top, right, bottom = text_box
        box_width = right - left
        box_height = bottom - top

        font = self._get_fitted_font(
            draw,
            word,
            box_width - 20,
            box_height - 10
        )

        bbox = draw.textbbox(
            (0, 0),
            word,
            font=font
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = left + (box_width - text_width) / 2
        y = top + (box_height - text_height) / 2 - 4

        draw.text(
            (x, y),
            word,
            fill=(25, 33, 56),
            font=font
        )

    def _get_fitted_font(
        self,
        draw,
        text,
        max_width,
        max_height
    ):
        for size in range(28, 15, -1):
            font = self._load_font(size)

            bbox = draw.textbbox(
                (0, 0),
                text,
                font=font
            )

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if (
                text_width <= max_width
                and text_height <= max_height
            ):
                return font

        return self._load_font(16)

    def _load_font(self, size):
        possible_fonts = [
            "arialbd.ttf",
            "Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
        ]

        for font_name in possible_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _normalize_name(self, name):
        name = name.strip().lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        return name.strip("_")