import json
from pathlib import Path

from audio_engine.audio_file_validator import (
    AudioFileValidator
)


class Stage1ReadinessAssessor:

    REQUIRED_AUDIO_NAMES = (
        "pronunciation",
        "meaning",
        "present_sentence",
        "past_sentence",
        "future_sentence"
    )

    READY_MEDIA_STATUSES = {
        "selected",
        "fallback_selected"
    }

    MEDIA_PROBLEM_STATUSES = {
        "media_missing",
        "verification_unavailable",
        "error"
    }

    def assess(
        self,
        lesson,
        lesson_folder
    ):

        lesson_folder = Path(
            lesson_folder
        )

        content_ready, content_issue = (
            self._assess_content(
                lesson,
                lesson_folder
            )
        )

        media_ready = True
        audio_ready = True
        problem_words = []

        for word in lesson.words:
            media_issue = self._media_issue(
                word,
                lesson_folder
            )

            if media_issue is not None:
                media_ready = False
                problem_words.append({
                    "word": word.word,
                    "component": "media",
                    "issue": media_issue
                })

            audio_issue = self._audio_issue(
                word,
                lesson_folder
            )

            if audio_issue is not None:
                audio_ready = False
                problem_words.append({
                    "word": word.word,
                    "component": "audio",
                    "issue": audio_issue
                })

        ready_for_presentation = (
            content_ready
            and media_ready
            and audio_ready
        )

        return {
            "content": (
                "ready"
                if content_ready
                else "incomplete"
            ),
            "media": (
                "ready"
                if media_ready
                else "incomplete"
            ),
            "audio": (
                "ready"
                if audio_ready
                else "incomplete"
            ),
            "content_issue": content_issue,
            "problem_words": problem_words,
            "overall": (
                "ready"
                if ready_for_presentation
                else "completed_with_issues"
            ),
            "ready_for_presentation": (
                ready_for_presentation
            )
        }

    def _assess_content(
        self,
        lesson,
        lesson_folder
    ):

        verification = getattr(
            lesson,
            "content_verification",
            {}
        ) or {}

        if "passed" in verification:
            if verification["passed"]:
                return True, None

            return (
                False,
                "content_verification_failed"
            )

        previous_readiness = getattr(
            lesson,
            "stage1_readiness",
            {}
        ) or {}

        if previous_readiness.get("content") == "ready":
            return True, None

        corrected_report = (
            lesson_folder
            / "verification"
            / "corrected_verification_report.json"
        )

        if corrected_report.is_file():
            try:
                with open(
                    corrected_report,
                    "r",
                    encoding="utf-8"
                ) as file:
                    report = json.load(file)

                errors = report.get(
                    "summary",
                    {}
                ).get("errors")

                if errors == 0:
                    return True, None

                if errors is not None:
                    return (
                        False,
                        "content_verification_failed"
                    )

            except (
                OSError,
                ValueError,
                TypeError
            ):
                pass

        return (
            False,
            "content_verification_missing"
        )

    def _media_issue(
        self,
        word,
        lesson_folder
    ):

        status = getattr(
            word,
            "media_status",
            None
        )

        if status in self.MEDIA_PROBLEM_STATUSES:
            return status

        if status not in self.READY_MEDIA_STATUSES:
            return "media_incomplete"

        media_type = getattr(
            word,
            "media_type",
            None
        )

        if media_type == "video":
            media_paths = (
                getattr(word, "default_video", None),
                getattr(word, "default_image", None)
            )
        elif media_type in (
            "photo",
            "illustration"
        ):
            media_paths = (
                getattr(word, "default_image", None),
            )
        else:
            return "invalid_selected_media"

        if not all(
            self._is_valid_file(
                saved_path,
                lesson_folder
            )
            for saved_path in media_paths
        ):
            return "invalid_selected_media"

        return None

    def _audio_issue(
        self,
        word,
        lesson_folder
    ):

        audio_folder = getattr(
            word,
            "audio_folder",
            None
        )

        if not audio_folder:
            missing = list(
                self.REQUIRED_AUDIO_NAMES
            )
        else:
            folder_path = self._resolve_path(
                audio_folder,
                lesson_folder
            )

            missing = [
                audio_name
                for audio_name
                in self.REQUIRED_AUDIO_NAMES
                if not AudioFileValidator.is_valid_mp3(
                    folder_path / f"{audio_name}.mp3"
                )
            ]

        if not missing:
            return None

        return (
            "audio_missing: "
            + ", ".join(missing)
        )

    @classmethod
    def _is_valid_file(
        cls,
        saved_path,
        lesson_folder
    ):

        if not saved_path:
            return False

        path = cls._resolve_path(
            saved_path,
            lesson_folder
        )

        try:
            return (
                path.is_file()
                and path.stat().st_size > 0
            )
        except OSError:
            return False

    @staticmethod
    def _resolve_path(
        saved_path,
        lesson_folder
    ):

        path = Path(saved_path)

        if path.exists() or path.is_absolute():
            return path

        return Path(lesson_folder) / path

    @staticmethod
    def print_report(readiness):

        print("\nSTAGE 1 READINESS")
        print(
            "Content: "
            f"{readiness['content'].upper()}"
        )
        print(
            "Media: "
            f"{readiness['media'].upper()}"
        )
        print(
            "Audio: "
            f"{readiness['audio'].upper()}"
        )

        content_issue = readiness.get(
            "content_issue"
        )

        if content_issue:
            print(
                "\nContent issue: "
                f"{content_issue}"
            )

        problem_words = readiness.get(
            "problem_words",
            []
        )

        if problem_words:
            print("\nProblem words:")

            for problem in problem_words:
                print(
                    f"{problem['word']} -> "
                    f"{problem['issue']}"
                )

        print("\nOverall:")

        if readiness["ready_for_presentation"]:
            print("COMPLETED")
            print("READY FOR PRESENTATION")
        else:
            print("COMPLETED WITH ISSUES")
            print("NOT READY FOR PRESENTATION")
