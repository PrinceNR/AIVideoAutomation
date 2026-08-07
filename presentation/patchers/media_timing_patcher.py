from pathlib import Path
import re


class MediaTimingPatcher:

    def patch(
        self,
        slides_folder: Path
    ):

        slide_files = sorted(
            slides_folder.glob("slide*.xml")
        )

        for slide_file in slide_files:

            xml = slide_file.read_text(
                encoding="utf-8"
            )

            # Only process slides containing media
            if "<p:timing>" not in xml:
                continue

            print(
                f"Processing {slide_file.name}"
            )