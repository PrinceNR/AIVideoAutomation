from pathlib import Path

from presentation.automation.powerpoint_controller import (
    PowerPointController
)


class ThumbnailPngExporter:

    def export(
        self,
        pptx_path,
        output_path,
        width=1280,
        height=720
    ):

        pptx_path = Path(
            pptx_path
        ).resolve()

        output_path = Path(
            output_path
        ).resolve()

        if not pptx_path.exists():

            raise FileNotFoundError(
                f"Thumbnail PPTX not found: "
                f"{pptx_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if output_path.exists():
            output_path.unlink()

        with PowerPointController(
            visible=True
        ) as ppt:

            ppt.open_presentation(
                pptx_path
            )

            slide = (
                ppt.presentation.Slides(1)
            )

            print(
                "Exporting thumbnail PNG..."
            )

            slide.Export(
                str(output_path),
                "PNG",
                width,
                height
            )

        if not output_path.exists():

            raise RuntimeError(
                "PowerPoint did not create "
                "the thumbnail PNG."
            )

        size = output_path.stat().st_size

        if size == 0:

            raise RuntimeError(
                "Thumbnail PNG was created "
                "but is empty."
            )

        print(
            f"PNG thumbnail created: "
            f"{output_path}"
        )

        return output_path