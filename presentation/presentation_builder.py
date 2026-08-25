from dataclasses import dataclass

from presentation.template_loader import TemplateLoader
from presentation.slide_group_renderer import SlideGroupRenderer
from presentation.slide_group_duplicator import SlideGroupDuplicator
from presentation.slide_group_manager import SlideGroupManager
from presentation.template_definition_loader import TemplateDefinitionLoader
from presentation.postprocessor.pptx_post_processor import PptxPostProcessor
from presentation.audio_presentation_processor import AudioPresentationProcessor
from presentation.video_presentation_processor import VideoPresentationProcessor
from presentation.animations.visual_animation_presentation_processor import (
    VisualAnimationPresentationProcessor,
)
from presentation.presentation_logger import (
    presentation_logger as log,
)


@dataclass(frozen=True)
class PresentationBuildSummary:
    slides: int
    audio_files: int
    video_clips: int
    animation_slides: int
    timed_slides: int




class PresentationBuilder:

    def __init__(self):

        self.loader = TemplateLoader()
        self.duplicator = SlideGroupDuplicator()
        self.renderer = SlideGroupRenderer() 
        self.manager = SlideGroupManager()   
        self.template_loader = TemplateDefinitionLoader()
        self.post_processor = PptxPostProcessor() 
        self.audio_presentation_processor = AudioPresentationProcessor()
        self.video_presentation_processor = VideoPresentationProcessor()
        self.visual_animation_processor = (
            VisualAnimationPresentationProcessor()
        )

    def get_slide_count(self, lesson):
        template_definition = self.template_loader.load(
            "templates/vocabulary/template_definition.json"
        )

        return (
            len(lesson.words)
            * template_definition.slides_per_word
        )

    def build(
        self,
        lesson,
        template_path,
        output_path
    ):
        template_definition = self.template_loader.load(
            "templates/vocabulary/template_definition.json"
        )
        presentation = self.loader.load(
            template_path
        )

        log.detail(
            "Slides per word: "
            f"{template_definition.slides_per_word}"
        )
    
        # Duplicate remaining groups
        for _ in range(len(lesson.words) - 1):

            self.duplicator.duplicate_group(
                presentation,
                0,
                template_definition.slides_per_word
            )

        # Render every word
        for index, word in enumerate(lesson.words):

            slides = self.manager.get_group(
                presentation,
                index
            )

            self.renderer.render(
                slides,
                template_definition.slides,
                word,               
                index + 1,
                len(lesson.words)
            )

            # timelines = self.renderer.render(
            #     slides,
            #     template_definition.slides,
            #     word,
            #     index + 1,
            #     len(lesson.words)
            # )

        presentation.save(output_path)

        self.post_processor.process(
            output_path
        )

        log.detail("Base presentation created.")

        # -------------------------------------------------
        # Embed audio and apply slide timings
        # -------------------------------------------------

        audio_summary = self.audio_presentation_processor.process(
            pptx_path=output_path,
            lesson=lesson,
            template_definition=template_definition
        )

        video_clips = self.video_presentation_processor.process(
            pptx_path=output_path,
            lesson=lesson,
            template_definition=template_definition
        )

        # Append conservative visual effects only after
        # audio timing and video embedding are complete.
        animation_slides = self.visual_animation_processor.process(
            pptx_path=output_path,
            template_path=template_path,
        )

        if video_clips:
            self.video_presentation_processor.verify_saved_video_playback(
                output_path,
                verify_teaching_timeline=False,
            )

        log.detail("Presentation created successfully!")

        return PresentationBuildSummary(
            slides=(
                len(lesson.words)
                * template_definition.slides_per_word
            ),
            audio_files=audio_summary["audio_files"],
            video_clips=video_clips,
            animation_slides=animation_slides,
            timed_slides=audio_summary["timed_slides"],
        )
