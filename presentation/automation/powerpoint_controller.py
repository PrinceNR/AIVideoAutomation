from presentation.automation.audio_controller import AudioController
from pathlib import Path
import pythoncom
import win32com.client


class PowerPointController:
    """
    Controls Microsoft PowerPoint through COM.
    """

    def __init__(self, visible=False):
        self.visible = visible
        self.app = None
        self.presentation = None

    def open(self):
        pythoncom.CoInitialize()

        self.app = win32com.client.Dispatch("PowerPoint.Application")
        self.app.Visible = self.visible

    def open_presentation(self, pptx_path: str | Path):
        pptx_path = str(Path(pptx_path).resolve())

        self.presentation = self.app.Presentations.Open(
            pptx_path,
            WithWindow=self.visible
        )
        self.audio = AudioController(self.presentation)

    def save(self):
        if self.presentation:
            self.presentation.Save()

    def save_as(self, output_path: str):
        self.presentation.SaveAs(str(output_path))

    # def close(self):
    #     if self.presentation:
    #         self.presentation.Close()
    #         self.presentation = None

    def close(self):
        try:
            if self.presentation:
                self.presentation.Close()
        except Exception:
            pass

        self.presentation = None

    def quit(self):
        try:
            if self.app:
                self.app.Quit()
        except Exception:
            pass

        self.app = None
        pythoncom.CoUninitialize()

    # def quit(self):
    #     if self.app:
    #         self.app.Quit()
    #         self.app = None

    #     pythoncom.CoUninitialize()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        self.quit()