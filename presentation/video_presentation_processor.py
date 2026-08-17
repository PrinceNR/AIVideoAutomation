from pathlib import Path

from presentation.automation.powerpoint_controller import (
    PowerPointController
)
from presentation.embedders.video_embedder import (
    VideoEmbedder
)
from presentation.com_visual_slot_locator import (
    ComVisualSlotLocator
)


class VideoPresentationProcessor:

    def __init__(self):
        self.video_embedder = VideoEmbedder()
        self.locator = ComVisualSlotLocator()

    def process(
        self,
        pptx_path,
        lesson,
        template_definition
    ):
        pptx_path = Path(pptx_path).resolve()

        print("=" * 70)
        print("COM VIDEO EMBEDDING")
        print("=" * 70)

        with PowerPointController(visible=True) as ppt:

            ppt.open_presentation(
                pptx_path
            )

            presentation = ppt.presentation
            slide_index = 1

            for word in lesson.words:

                print(f"\nWord: {word.word}")

                for slide_definition in template_definition.slides:

                    slide = presentation.Slides(
                        slide_index
                    )

                    if self._should_embed_video(
                        word,
                        slide_definition
                    ):
                        self._replace_picture_with_video(
                            slide=slide,
                            word=word,
                            slide_index=slide_index,
                            slide_type=slide_definition.type
                        )

                    slide_index += 1

            ppt.save()

        print("\nCOM video embedding completed.")

    def _should_embed_video(
        self,
        word,
        slide_definition
    ):
        if getattr(
            word,
            "media_type",
            None
        ) != "video":
            return False

        if not getattr(
            word,
            "default_video",
            None
        ):
            return False

        if (
            "image"
            not in slide_definition.processors
        ):
            return False

        return True

    def _replace_picture_with_video(
        self,
        slide,
        word,
        slide_index,
        slide_type
    ):
        picture = self.locator.find_picture(
            slide
        )

        if picture is None:
            print(
                f"  Slide {slide_index} "
                f"({slide_type}): "
                f"no image placeholder found."
            )
            return

        left = picture.left
        top = picture.top
        width = picture.width
        height = picture.height

        original_z_order = (
            picture.ZOrderPosition
        )

        picture.Delete()

        media_shape = self.video_embedder.embed(
            slide=slide,
            video_path=word.default_video,
            left=left,
            top=top,
            width=width,
            height=height
        )

        self._restore_z_order(
            media_shape,
            original_z_order
        )

        print(
            f"  Slide {slide_index} "
            f"({slide_type}): "
            f"embedded video -> {word.default_video}"
        )

    @staticmethod
    def _restore_z_order(
        shape,
        target_position
    ):

        # PowerPoint adds new shapes at the front.
        # Move the video backward until it reaches
        # the same layer as the original picture.

        while (
            shape.ZOrderPosition
            > target_position
        ):

            shape.ZOrder(3)