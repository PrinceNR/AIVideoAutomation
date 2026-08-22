from pathlib import Path
from presentation.patchers.relationship_patcher import RelationshipPatcher
from presentation.patchers.slide_xml_patcher import SlideXmlPatcher
from presentation.patchers.media_timing_patcher import MediaTimingPatcher
from presentation.presentation_logger import (
    presentation_logger as log,
)


class PresentationPatcher:

    def __init__(self):

        self.relationship_patcher = RelationshipPatcher()
        self.slide_xml_patcher = SlideXmlPatcher()
        self.media_timing_patcher = MediaTimingPatcher()

    def patch(
        self,
        temp_folder: Path
    ):

        slides_folder = (
            temp_folder
            / "ppt"
            / "slides"
        )

        rels_folder = (
            slides_folder
            / "_rels"
        )

        log.detail(str(slides_folder))

        log.detail(str(rels_folder))

        self.media_timing_patcher.patch(
            slides_folder
        )
