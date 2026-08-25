from dataclasses import dataclass
from pathlib import Path
import re
from xml.etree import ElementTree

from presentation.animations.visual_animation_planner import (
    AnimationTemplateError,
)
from presentation.presentation_logger import (
    presentation_logger as log,
)


@dataclass(frozen=True)
class SentenceLetterTimingVerification:
    shape_name: str
    shape_id: int
    letter_delay_ms: int


class SentenceLetterTimingPatcher:
    """Sets the exact PowerPoint by-letter interval after COM saves."""

    PRESENTATION_NS = (
        "http://schemas.openxmlformats.org/"
        "presentationml/2006/main"
    )
    ITERATE_PATTERN = re.compile(
        r'(?P<open><p:iterate\b[^>]*\btype="lt"[^>]*>)'
        r'.*?'
        r'(?P<close></p:iterate>)',
        flags=re.DOTALL,
    )

    def patch(
        self,
        slides_folder: Path,
        slide_targets: dict[int, str],
        letter_delay: float,
    ):
        milliseconds = max(
            1,
            round(float(letter_delay) * 1000.0),
        )
        patched_count = 0

        for slide_number, shape_name in sorted(
            slide_targets.items()
        ):
            slide_path = (
                Path(slides_folder)
                / f"slide{slide_number}.xml"
            )

            if not slide_path.is_file():
                raise AnimationTemplateError(
                    "Cannot configure handwriting timing because "
                    f"slide XML is missing: {slide_path.name}."
                )

            xml = slide_path.read_text(encoding="utf-8")
            patched_xml = self.patch_slide_xml(
                xml,
                shape_name,
                milliseconds,
            )
            slide_path.write_text(
                patched_xml,
                encoding="utf-8",
            )
            patched_count += 1

        log.detail(
            "Configured exact by-letter timing for "
            f"{patched_count} sentence animation(s)."
        )
        return patched_count

    def verify(
        self,
        slides_folder: Path,
        slide_targets: dict[int, str],
        letter_delay: float,
        expected_shape_ids: dict[int, int] | None = None,
    ):
        milliseconds = max(
            1,
            round(float(letter_delay) * 1000.0),
        )
        expected_shape_ids = expected_shape_ids or {}
        verified = {}

        for slide_number, shape_name in sorted(
            slide_targets.items()
        ):
            slide_path = (
                Path(slides_folder)
                / f"slide{slide_number}.xml"
            )

            if not slide_path.is_file():
                raise AnimationTemplateError(
                    "Cannot verify handwriting timing because "
                    f"slide XML is missing: {slide_path.name}."
                )

            state = self.verify_slide_xml(
                slide_path.read_text(encoding="utf-8"),
                shape_name,
                milliseconds,
                expected_shape_id=expected_shape_ids.get(
                    slide_number
                ),
            )
            verified[slide_number] = state

            log.detail(
                f"  Slide {slide_number}: saved XML targets "
                f"{shape_name} shape ID {state.shape_id}; "
                f"Fade-by-letter={state.letter_delay_ms}ms."
            )

        return verified

    def patch_slide_xml(
        self,
        xml: str,
        shape_name: str,
        milliseconds: int,
    ):
        root = self._parse_slide_xml(xml)
        namespace = f"{{{self.PRESENTATION_NS}}}"
        shape_id = self._semantic_shape_id(
            root,
            namespace,
            shape_name,
        )
        iterates = [
            element
            for element in root.iter(f"{namespace}iterate")
            if element.get("type") == "lt"
        ]
        candidates = self._fade_letter_iterates(
            root,
            namespace,
            shape_id,
        )

        if len(candidates) != 1:
            raise AnimationTemplateError(
                "PowerPoint timing patch requires exactly one "
                "Fade-by-letter effect for semantic shape "
                f"'{shape_name}'; found {len(candidates)}."
            )

        target_index = iterates.index(candidates[0])
        matches = list(self.ITERATE_PATTERN.finditer(xml))

        if len(matches) != len(iterates):
            raise AnimationTemplateError(
                "PowerPoint by-letter timing nodes could not be "
                "matched safely without changing unrelated effects."
            )

        target_match = matches[target_index]
        replacement = (
            f"{target_match.group('open')}"
            f'<p:tmAbs val="{int(milliseconds)}"/>'
            f"{target_match.group('close')}"
        )
        return (
            xml[:target_match.start()]
            + replacement
            + xml[target_match.end():]
        )

    def verify_slide_xml(
        self,
        xml: str,
        shape_name: str,
        milliseconds: int,
        expected_shape_id: int | None = None,
    ):
        root = self._parse_slide_xml(xml)
        namespace = f"{{{self.PRESENTATION_NS}}}"
        shape_id = self._semantic_shape_id(
            root,
            namespace,
            shape_name,
        )

        if (
            expected_shape_id is not None
            and int(shape_id) != int(expected_shape_id)
        ):
            raise AnimationTemplateError(
                "Saved PowerPoint sentence shape ID changed for "
                f"'{shape_name}': expected {expected_shape_id}, "
                f"found {shape_id}."
            )

        candidates = self._fade_letter_iterates(
            root,
            namespace,
            shape_id,
        )

        if len(candidates) != 1:
            raise AnimationTemplateError(
                "Saved PowerPoint XML requires exactly one "
                "Fade-by-letter effect for semantic shape "
                f"'{shape_name}'; found {len(candidates)}."
            )

        timing_nodes = list(candidates[0])
        absolute_timings = [
            node
            for node in timing_nodes
            if node.tag == f"{namespace}tmAbs"
        ]

        if len(absolute_timings) != 1:
            raise AnimationTemplateError(
                "Saved PowerPoint XML did not preserve exact "
                f"by-letter timing for '{shape_name}'."
            )

        try:
            saved_milliseconds = int(
                absolute_timings[0].get("val")
            )
        except (TypeError, ValueError) as error:
            raise AnimationTemplateError(
                "Saved PowerPoint by-letter timing is invalid for "
                f"'{shape_name}'."
            ) from error

        if saved_milliseconds != int(milliseconds):
            raise AnimationTemplateError(
                "Saved PowerPoint by-letter timing changed for "
                f"'{shape_name}': expected {int(milliseconds)}ms, "
                f"found {saved_milliseconds}ms."
            )

        reveal_masks = [
            element.get("name", "")
            for element in root.iter(f"{namespace}cNvPr")
            if "REVEAL_MASK" in element.get("name", "")
        ]

        if reveal_masks:
            raise AnimationTemplateError(
                "Saved PowerPoint handwriting contains reveal-mask "
                f"shape(s): {', '.join(reveal_masks)}."
            )

        return SentenceLetterTimingVerification(
            shape_name=shape_name,
            shape_id=int(shape_id),
            letter_delay_ms=saved_milliseconds,
        )

    @staticmethod
    def _parse_slide_xml(xml):
        try:
            return ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise AnimationTemplateError(
                "PowerPoint sentence timing XML is malformed."
            ) from error

    @staticmethod
    def _semantic_shape_id(
        root,
        namespace,
        shape_name,
    ):
        shape_ids = {
            element.get("id")
            for element in root.iter(f"{namespace}cNvPr")
            if element.get("name") == shape_name
        }

        if len(shape_ids) != 1:
            raise AnimationTemplateError(
                "PowerPoint timing requires exactly one semantic "
                f"shape '{shape_name}'; found {len(shape_ids)}."
            )

        return next(iter(shape_ids))

    @staticmethod
    def _fade_letter_iterates(
        root,
        namespace,
        shape_id,
    ):
        iterates = [
            element
            for element in root.iter(f"{namespace}iterate")
            if element.get("type") == "lt"
        ]
        candidates = []
        parent_map = {
            child: parent
            for parent in root.iter()
            for child in parent
        }

        for iterate in iterates:
            effect_timing = parent_map.get(iterate)

            if effect_timing is None:
                continue

            is_fade_entrance = (
                effect_timing.tag == f"{namespace}cTn"
                and effect_timing.get("presetID") == "10"
                and effect_timing.get("presetClass") == "entr"
                and any(
                    animation.get("filter") == "fade"
                    and animation.get("transition") == "in"
                    for animation in effect_timing.iter(
                        f"{namespace}animEffect"
                    )
                )
            )
            targets_shape = any(
                target.get("spid") == shape_id
                for target in effect_timing.iter(
                    f"{namespace}spTgt"
                )
            )

            if is_fade_entrance and targets_shape:
                candidates.append(iterate)

        return candidates
