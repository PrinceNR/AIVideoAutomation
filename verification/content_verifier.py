from pathlib import Path
import sys

from models.lesson_mapper import (
    LessonMapper
)

from utils.file_manager import (
    FileManager
)

from verification.lesson_verifier import (
    LessonVerifier
)

from verification.semantic_lesson_verifier import (
    SemanticLessonVerifier
)

from ai.content_generator import (
    build_vocabulary_prompt
)


class ContentVerifier:

    def __init__(self):

        self.file_manager = FileManager()

        self.rule_verifier = (
            LessonVerifier()
        )

        self.semantic_verifier = (
            SemanticLessonVerifier()
        )

    # =================================================
    # RULE DIAGNOSTICS
    # =================================================

    @classmethod
    def _print_rule_issues(
        cls,
        report,
        lesson_dict,
        heading="Content verification issues",
    ):

        errors = cls._issues_at_level(
            report,
            "error",
        )
        warnings = cls._issues_at_level(
            report,
            "warning",
        )

        if not errors and not warnings:
            return

        print(f"\n{heading}:")

        if errors:
            print("\nERRORS")

            for word_name, issue in errors:
                field = issue.get("field") or "lesson"
                reason = (
                    issue.get("message")
                    or issue.get("reason")
                    or "Rule-based verification failed."
                )
                value = cls._lesson_field_value(
                    lesson_dict,
                    word_name,
                    field,
                )

                print(
                    f"word: {word_name or 'lesson-level'}"
                )
                print(f"field: {field}")
                print(
                    "rule: "
                    f"{cls._rule_label(field, reason)}"
                )

                if value is not None:
                    print(
                        "value: "
                        f"{cls._terminal_safe_text(value)}"
                    )

                print(f"reason: {reason}")

        if warnings:
            print("\nWarnings:")

            for word_name, issue in warnings:
                field = issue.get("field") or "lesson"
                reason = (
                    issue.get("message")
                    or issue.get("reason")
                    or "Rule-based verification warning."
                )
                print(
                    f"{word_name or 'lesson-level'} / "
                    f"{field}: {reason}"
                )

    @staticmethod
    def _issues_at_level(report, level):

        return [
            (result.get("word", ""), issue)
            for result in report.get("results", [])
            for issue in result.get("issues", [])
            if issue.get("level") == level
        ]

    @staticmethod
    def _lesson_field_value(
        lesson_dict,
        word_name,
        field,
    ):

        if not word_name:
            return None

        word = next(
            (
                item
                for item in lesson_dict.get("words", [])
                if str(item.get("word", "")).lower()
                == str(word_name).lower()
            ),
            None,
        )

        if word is None:
            return None

        value = word

        for part in str(field).split("."):
            if not isinstance(value, dict):
                return None

            value = value.get(part)

        return value

    @staticmethod
    def _rule_label(field, reason):

        reason_text = str(reason).lower()

        if (
            str(field).startswith("translations.")
            and "script characters" in reason_text
        ):
            return "translation_native_script"

        if (
            str(field).endswith("_sentence")
            and "expected 7 to 15 words" in reason_text
        ):
            return "sentence_word_count"

        return "rule_based_validation"

    @staticmethod
    def _terminal_safe_text(value):

        text = str(value)
        encoding = getattr(
            sys.stdout,
            "encoding",
            None,
        ) or "utf-8"

        return text.encode(
            encoding,
            errors="backslashreplace",
        ).decode(encoding)

    # =================================================
    # PREPARE DEEPSEEK CORRECTED LESSON
    # =================================================

    def _prepare_corrected_lesson(
        self,
        original_lesson,
        corrected_lesson
    ):

        if not isinstance(
            corrected_lesson,
            dict
        ):

            return None

        original_words = (
            original_lesson.get(
                "words",
                []
            )
        )

        corrected_words = (
            corrected_lesson.get(
                "words",
                []
            )
        )

        # ---------------------------------------------
        # Word count must remain unchanged
        # ---------------------------------------------

        if (
            len(original_words)
            != len(corrected_words)
        ):

            print(
                "DeepSeek changed the number "
                "of vocabulary words."
            )

            return None

        # ---------------------------------------------
        # Word names and order must remain unchanged
        # ---------------------------------------------

        for original, corrected in zip(
            original_words,
            corrected_words
        ):

            original_word = (
                original.get(
                    "word",
                    ""
                )
                .strip()
                .lower()
            )

            corrected_word = (
                corrected.get(
                    "word",
                    ""
                )
                .strip()
                .lower()
            )

            if (
                original_word
                != corrected_word
            ):

                print(
                    f"DeepSeek replaced vocabulary word: "
                    f"{original_word} -> {corrected_word}"
                )

        # ---------------------------------------------
        # Preserve lesson metadata
        # ---------------------------------------------

        corrected_lesson["title"] = (
            original_lesson.get(
                "title",
                ""
            )
        )

        corrected_lesson["topic"] = (
            original_lesson.get(
                "topic",
                ""
            )
        )

        corrected_lesson["suggestions"] = (
            original_lesson.get(
                "suggestions",
                ""
            )
        )

        # ---------------------------------------------
        # DeepSeek must not modify media information
        # ---------------------------------------------

        media_fields = [
            "image_folder",
            "audio_folder",
            "default_audio",
            "default_image"
        ]

        for original, corrected in zip(
            original_words,
            corrected_words
        ):

            original_word = (
                original.get(
                    "word",
                    ""
                )
                .strip()
                .lower()
            )

            corrected_word = (
                corrected.get(
                    "word",
                    ""
                )
                .strip()
                .lower()
            )

            # Same vocabulary word:
            # preserve existing media information.
            if (
                original_word
                == corrected_word
            ):

                for field in media_fields:

                    corrected[field] = (
                        original.get(
                            field
                        )
                    )

            # Vocabulary word was replaced:
            # old media must NOT belong to the new word.
            else:

                corrected["image_folder"] = None
                corrected["audio_folder"] = None
                corrected["default_audio"] = None
                corrected["default_image"] = None

        return corrected_lesson

    # =================================================
    # VERIFY
    # =================================================

    def verify(
        self,
        lesson_path
    ):

        lesson_path = Path(
            lesson_path
        )

        print(
            "\nVerifying generated lesson..."
        )

        lesson = (
            self.file_manager.load_lesson(
                lesson_path
            )
        )

        lesson_dict = (
            LessonMapper.to_dict(
                lesson
            )
        )

        verification_folder = (
            lesson_path.parent /
            "verification"
        )

        verification_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # =================================================
        # BUILD EXACT GENERATION PROMPT FOR DEEPSEEK
        # =================================================

        generation_prompt = (
            build_vocabulary_prompt(
                topic=lesson.topic,
                count=len(
                    lesson.words
                ),
                suggestions=lesson.suggestions
            )
        )

        # =================================================
        # 1. ORIGINAL RULE-BASED VERIFICATION
        # =================================================

        print(
            "Running rule-based verification..."
        )

        rule_report = (
            self.rule_verifier.verify(
                lesson
            )
        )

        rule_report_path = (
            verification_folder /
            "verification_report.json"
        )

        self.file_manager.save_json(
            rule_report,
            rule_report_path
        )

        rule_summary = (
            rule_report.get(
                "summary",
                {}
            )
        )

        print(
            f"  Passed: "
            f"{rule_summary.get('passed', 0)}"
        )

        print(
            f"  Warnings: "
            f"{rule_summary.get('warnings', 0)}"
        )

        print(
            f"  Errors: "
            f"{rule_summary.get('errors', 0)}"
        )

        if rule_summary.get("errors", 0) > 0:
            self._print_rule_issues(
                rule_report,
                lesson_dict,
            )
            print(
                "\nAttempting one bounded correction pass..."
            )

        # =================================================
        # 2. DEEPSEEK SEMANTIC VERIFICATION
        # =================================================

        print(
            "\nRunning DeepSeek semantic verification..."
        )

        semantic_report = (
            self.semantic_verifier.verify(
                lesson_dict,
                generation_prompt=
                    generation_prompt,
                rule_report=rule_report,
            )
        )

        semantic_report_path = (
            verification_folder /
            "semantic_verification_report.json"
        )

        self.file_manager.save_json(
            semantic_report,
            semantic_report_path
        )

        semantic_summary = (
            semantic_report.get(
                "summary",
                {}
            )
        )

        semantic_passed = (
            semantic_summary.get(
                "passed",
                0
            )
        )

        semantic_warnings = (
            semantic_summary.get(
                "warnings",
                0
            )
        )

        semantic_errors = (
            semantic_summary.get(
                "errors",
                0
            )
        )

        print(
            f"  Passed: "
            f"{semantic_passed}"
        )

        print(
            f"  Warnings: "
            f"{semantic_warnings}"
        )

        print(
            f"  Errors: "
            f"{semantic_errors}"
        )

        # =================================================
        # 3. PREPARE CORRECTED LESSON
        # =================================================

        corrected_lesson = (
            semantic_report.get(
                "corrected_lesson"
            )
        )

        corrected_lesson = (
            self._prepare_corrected_lesson(
                lesson_dict,
                corrected_lesson
            )
        )

        if corrected_lesson is None:

            print(
                "\nDeepSeek did not return a "
                "safe corrected lesson."
            )

            return {
                "passed": False,

                "has_warnings": (
                    rule_summary.get(
                        "warnings",
                        0
                    ) > 0
                    or
                    semantic_warnings > 0
                ),

                "rule_errors":
                    rule_summary.get(
                        "errors",
                        0
                    ),

                "semantic_errors":
                    semantic_errors,

                "corrected_lesson":
                    None,

                "rule_report":
                    rule_report_path,

                "semantic_report":
                    semantic_report_path,

                "corrected_rule_report":
                    None
            }

        # =================================================
        # 4. VERIFY DEEPSEEK CORRECTED LESSON
        # =================================================

        print(
            "\nChecking DeepSeek corrected lesson..."
        )

        corrected_lesson_object = (
            LessonMapper.from_dict(
                corrected_lesson
            )
        )

        corrected_rule_report = (
            self.rule_verifier.verify(
                corrected_lesson_object
            )
        )

        corrected_rule_report_path = (
            verification_folder /
            "corrected_verification_report.json"
        )

        self.file_manager.save_json(
            corrected_rule_report,
            corrected_rule_report_path
        )

        corrected_summary = (
            corrected_rule_report.get(
                "summary",
                {}
            )
        )

        corrected_passed = (
            corrected_summary.get(
                "passed",
                0
            )
        )

        corrected_warnings = (
            corrected_summary.get(
                "warnings",
                0
            )
        )

        corrected_errors = (
            corrected_summary.get(
                "errors",
                0
            )
        )

        print(
            f"  Passed: "
            f"{corrected_passed}"
        )

        print(
            f"  Warnings: "
            f"{corrected_warnings}"
        )

        print(
            f"  Errors: "
            f"{corrected_errors}"
        )

        # =================================================
        # 5. FINAL DECISION
        # =================================================

        # IMPORTANT:
        #
        # DeepSeek may have found errors in the ORIGINAL
        # lesson and then corrected them.
        #
        # Therefore semantic_errors should NOT automatically
        # make the final lesson fail.
        #
        # We decide based on the corrected lesson.

        passed = (
            corrected_errors == 0
        )

        has_warnings = (
            corrected_warnings > 0
            or
            semantic_warnings > 0
        )

        print(
            "\nContent verification completed."
        )

        if not passed:

            print(
                "❌ Corrected lesson still "
                "contains verification errors."
            )
            self._print_rule_issues(
                corrected_rule_report,
                corrected_lesson,
                heading=(
                    "Unresolved content verification issues"
                ),
            )

        elif has_warnings:

            print(
                "⚠ Corrected lesson passed "
                "with warnings."
            )

        else:

            print(
                "✅ Corrected lesson passed "
                "verification."
            )

        return {
            "passed":
                passed,

            "has_warnings":
                has_warnings,

            "rule_errors":
                rule_summary.get(
                    "errors",
                    0
                ),

            "semantic_errors":
                semantic_errors,

            "corrected_rule_errors":
                corrected_errors,

            "corrected_lesson":
                corrected_lesson,

            "rule_report":
                rule_report_path,

            "semantic_report":
                semantic_report_path,

            "corrected_rule_report":
                corrected_rule_report_path
        }
