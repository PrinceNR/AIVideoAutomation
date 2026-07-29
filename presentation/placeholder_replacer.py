from pptx import Presentation


class PlaceholderReplacer:

    def replace_text(
        self,
        presentation: Presentation,
        placeholder: str,
        value: str
    ):

        for slide in presentation.slides:

            for shape in slide.shapes:

                if not shape.has_text_frame:
                    continue

                for paragraph in shape.text_frame.paragraphs:

                    for run in paragraph.runs:

                        if placeholder in run.text:

                            run.text = run.text.replace(
                                placeholder,
                                value
                            )