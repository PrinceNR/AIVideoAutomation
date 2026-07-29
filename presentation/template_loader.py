from pathlib import Path

from pptx import Presentation


class TemplateLoader:

    def load(self, template_path: Path) -> Presentation:

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}"
            )

        return Presentation(template_path)