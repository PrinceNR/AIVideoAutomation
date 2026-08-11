from pathlib import Path
import re
import tempfile

from PIL import Image, ImageOps
from pptx import Presentation


class ThumbnailPptxGenerator:

    MAX_WORDS = 8

    def generate(
        self,
        lesson,
        lesson_folder,
        template_path,
        output_path
    ):

        lesson_folder = Path(lesson_folder)
        template_path = Path(template_path)
        output_path = Path(output_path)

        if not template_path.exists():
            raise FileNotFoundError(
                f"Thumbnail template not found: {template_path}"
            )

        presentation = Presentation(template_path)

        if len(presentation.slides) == 0:
            raise ValueError(
                "Thumbnail template does not contain a slide."
            )

        slide = presentation.slides[0]

        print(
            f"Words available: {len(lesson.words)}"
        )

        words = lesson.words[:self.MAX_WORDS]

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_dir = Path(temp_dir)

            for index in range(1, self.MAX_WORDS + 1):

                image_placeholder = self._find_shape(
                    slide,
                    f"IMAGE_{index}"
                )

                word_placeholder = self._find_shape(
                    slide,
                    f"WORD_{index}"
                )

                if image_placeholder is None:
                    raise ValueError(
                        f"IMAGE_{index} not found in "
                        f"thumbnail template."
                    )

                if word_placeholder is None:
                    raise ValueError(
                        f"WORD_{index} not found in "
                        f"thumbnail template."
                    )

                # -----------------------------------------
                # Slot has a vocabulary word
                # -----------------------------------------

                if index <= len(words):

                    word = words[index - 1]

                    print(
                        f"Slot {index}: {word.word}"
                    )

                    # Replace sample text
                    self._replace_word_text(
                        word_placeholder,
                        word.word
                    )

                    # Find first available image
                    image_path = self._find_word_image(
                        lesson_folder,
                        word.word
                    )

                    if image_path is None:

                        print(
                            f"  Image not found: {word.word}"
                        )

                        continue

                    print(
                        f"  Image: {image_path}"
                    )

                    # Create properly cropped temporary image
                    cropped_image = (
                        temp_dir /
                        f"thumbnail_{index}.jpg"
                    )

                    self._prepare_image(
                        image_path=image_path,
                        output_path=cropped_image,
                        placeholder=image_placeholder,
                        presentation=presentation
                    )

                    # Add image exactly over IMAGE_X
                    slide.shapes.add_picture(
                        str(cropped_image),
                        image_placeholder.left,
                        image_placeholder.top,
                        image_placeholder.width,
                        image_placeholder.height
                    )

                # -----------------------------------------
                # Unused slot
                # -----------------------------------------

                else:

                    # Remove sample word from template
                    self._replace_word_text(
                        word_placeholder,
                        ""
                    )

        # ---------------------------------------------
        # Save editable PPTX
        # ---------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        presentation.save(output_path)

        print(
            f"Editable thumbnail PPTX created: "
            f"{output_path}"
        )

        return output_path

    # =================================================
    # Find shape by PowerPoint Selection Pane name
    # =================================================

    def _find_shape(self, slide, shape_name):

        for shape in slide.shapes:

            if shape.name == shape_name:
                return shape

        return None

    # =================================================
    # Replace word while trying to preserve template
    # formatting
    # =================================================

    def _replace_word_text(
        self,
        shape,
        text
    ):

        if not shape.has_text_frame:
            raise ValueError(
                f"{shape.name} is not a text box."
            )

        text_frame = shape.text_frame

        # Preserve the existing first run's formatting
        # whenever possible.
        if (
            text_frame.paragraphs
            and text_frame.paragraphs[0].runs
        ):

            first_paragraph = (
                text_frame.paragraphs[0]
            )

            first_run = (
                first_paragraph.runs[0]
            )

            first_run.text = text

            # Clear any additional runs
            for run in first_paragraph.runs[1:]:
                run.text = ""

            # Clear additional paragraphs
            for paragraph in text_frame.paragraphs[1:]:

                for run in paragraph.runs:
                    run.text = ""

        else:

            shape.text = text

    # =================================================
    # Find first image belonging to word
    # =================================================

    def _find_word_image(
        self,
        lesson_folder,
        word_name
    ):

        folder_name = self._normalize_name(
            word_name
        )

        word_folder = (
            lesson_folder
            / "images"
            / folder_name
        )

        if not word_folder.exists():
            return None

        extensions = [
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.webp"
        ]

        for extension in extensions:

            images = sorted(
                word_folder.glob(extension)
            )

            if images:
                return images[0]

        return None

    # =================================================
    # Crop image to same aspect ratio as placeholder
    # =================================================

    def _prepare_image(
        self,
        image_path,
        output_path,
        placeholder,
        presentation
    ):

        image = Image.open(
            image_path
        ).convert("RGB")

        # Calculate approximate output pixels using
        # our 1280 x 720 thumbnail canvas.

        target_width = max(
            1,
            round(
                placeholder.width
                / presentation.slide_width
                * 1280
            )
        )

        target_height = max(
            1,
            round(
                placeholder.height
                / presentation.slide_height
                * 720
            )
        )

        fitted = ImageOps.fit(
            image,
            (
                target_width,
                target_height
            ),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )

        fitted.save(
            output_path,
            quality=95
        )

    # =================================================
    # Folder-safe word name
    # =================================================

    def _normalize_name(
        self,
        name
    ):

        name = name.strip().lower()

        name = re.sub(
            r"[^a-z0-9]+",
            "_",
            name
        )

        return name.strip("_")