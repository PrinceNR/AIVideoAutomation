import json

from verification.deepseek_client import (
    DeepSeekClient
)

from verification.prompts import (
    LESSON_VERIFICATION_PROMPT
)


class SemanticLessonVerifier:

    def __init__(self):

        self.client = DeepSeekClient()

    # =================================================
    # VERIFY
    # =================================================

    def verify(
        self,
        lesson_dict,
        generation_prompt=""
    ):

        suggestions = lesson_dict.get(
            "suggestions",
            ""
        )

        lesson_json = json.dumps(
            lesson_dict,
            ensure_ascii=False,
            indent=2
        )

        prompt = (
            LESSON_VERIFICATION_PROMPT.format(
                suggestions=suggestions,
                generation_prompt=generation_prompt,
                lesson_json=lesson_json
            )
        )

        response_text = self.client.generate(
            prompt
        )

        response_text = (
            self._clean_json_response(
                response_text
            )
        )

        report = json.loads(
            response_text
        )

        # Validate DeepSeek's report
        # against the original lesson.
        report = self._validate_report(
            report,
            lesson_dict
        )

        report["model_used"] = (
            self.client.last_model_used
        )

        return report

    # =================================================
    # REPORT VALIDATION
    # =================================================

    def _validate_report(
        self,
        report,
        lesson_dict
    ):

        lesson_words = {
            word["word"].lower(): word
            for word in lesson_dict.get(
                "words",
                []
            )
        }

        validated_results = []
        discarded_issues = []

        for result in report.get(
            "results",
            []
        ):

            word_name = result.get(
                "word",
                ""
            )

            lesson_word = lesson_words.get(
                word_name.lower()
            )

            # -----------------------------------------
            # DeepSeek invented a vocabulary word
            # -----------------------------------------

            if lesson_word is None:

                discarded_issues.append({
                    "word": word_name,
                    "reason":
                        "Word does not exist in lesson."
                })

                continue

            valid_issues = []

            # -----------------------------------------
            # Validate every reported issue
            # -----------------------------------------

            for issue in result.get(
                "issues",
                []
            ):

                field = issue.get(
                    "field",
                    ""
                )

                current_value = issue.get(
                    "current_value"
                )

                actual_value = (
                    self._get_field_value(
                        lesson_word,
                        field
                    )
                )

                # -------------------------------------
                # First:
                # check that the reported value
                # really exists in lesson.json
                # -------------------------------------

                if not self._value_matches(
                    current_value,
                    actual_value
                ):

                    discarded_issues.append({
                        "word": word_name,
                        "field": field,
                        "reported_value":
                            current_value,
                        "actual_value":
                            actual_value,
                        "reason":
                            "Verifier reported a value "
                            "that does not match the lesson."
                    })

                    continue

                # -------------------------------------
                # Second:
                # catch self-contradictory corrections
                # -------------------------------------

                if self._is_self_contradictory_issue(
                    issue
                ):

                    discarded_issues.append({
                        "word": word_name,
                        "field": field,
                        "reported_value":
                            current_value,
                        "actual_value":
                            actual_value,
                        "reason":
                            "Verifier suggested the same "
                            "value as a valid correction."
                    })

                    continue

                # The issue passed grounding checks.
                valid_issues.append(
                    issue
                )

            # -----------------------------------------
            # Recalculate word status
            # -----------------------------------------

            has_error = any(
                issue.get("level") == "error"
                for issue in valid_issues
            )

            has_warning = any(
                issue.get("level") == "warning"
                for issue in valid_issues
            )

            if has_error:

                status = "error"

            elif has_warning:

                status = "warning"

            else:

                status = "passed"

            validated_results.append({
                "word": word_name,
                "status": status,
                "issues": valid_issues
            })

        # ---------------------------------------------
        # Recalculate summary
        # ---------------------------------------------

        passed = sum(
            1
            for item in validated_results
            if item["status"] == "passed"
        )

        warnings = sum(
            1
            for item in validated_results
            if item["status"] == "warning"
        )

        errors = sum(
            1
            for item in validated_results
            if item["status"] == "error"
        )

        report["results"] = (
            validated_results
        )

        report["summary"] = {
            "total_words":
                len(validated_results),

            "passed":
                passed,

            "warnings":
                warnings,

            "errors":
                errors
        }

        if errors > 0:

            report["overall_status"] = (
                "error"
            )

        elif warnings > 0:

            report["overall_status"] = (
                "warning"
            )

        else:

            report["overall_status"] = (
                "passed"
            )

        report["discarded_issues"] = (
            discarded_issues
        )

        return report

    # =================================================
    # SELF-CONTRADICTION CHECK
    # =================================================

    def _is_self_contradictory_issue(
        self,
        issue
    ):

        current = issue.get(
            "current_value"
        )

        suggested = issue.get(
            "suggested_value"
        )

        if not current:
            return False

        if not suggested:
            return False

        # Only compare strings here.
        if not isinstance(
            current,
            str
        ):
            return False

        if not isinstance(
            suggested,
            str
        ):
            return False

        current_normalized = (
            current.strip().lower()
        )

        suggested_normalized = (
            suggested.strip().lower()
        )

        # ---------------------------------------------
        # Exact same correction
        # ---------------------------------------------

        if (
            current_normalized
            == suggested_normalized
        ):
            return True

        # ---------------------------------------------
        # IPA special case
        #
        # Example:
        #
        # current:
        # /ˌmæn.jʊˈfæk.tʃər/
        #
        # suggested:
        # /ˌmæn.jʊˈfæk.tʃər/
        # or /ˌmæn.jəˈfæk.tʃɚ/
        #
        # Current pronunciation is already
        # included as a valid pronunciation.
        # ---------------------------------------------

        if (
            issue.get("field")
            == "pronunciation"
            and current_normalized
            in suggested_normalized
        ):
            return True

        return False

    # =================================================
    # FIELD LOOKUP
    # =================================================

    def _get_field_value(
        self,
        word,
        field
    ):

        value = word

        for part in field.split("."):

            if not isinstance(
                value,
                dict
            ):
                return None

            value = value.get(
                part
            )

        return value

    # =================================================
    # VALUE MATCHING
    # =================================================

    def _value_matches(
        self,
        reported,
        actual
    ):

        # Exact match
        if reported == actual:
            return True

        # DeepSeek may report only one
        # problematic item from a list.
        #
        # Example:
        #
        # actual:
        # ["applaud", "cheer", "pat"]
        #
        # reported:
        # "pat"
        if isinstance(
            actual,
            list
        ):

            if reported in actual:
                return True

        # Normalize strings
        if (
            isinstance(reported, str)
            and isinstance(actual, str)
        ):

            return (
                reported.strip().lower()
                ==
                actual.strip().lower()
            )

        return False

    # =================================================
    # JSON CLEANER
    # =================================================

    def _clean_json_response(
        self,
        text
    ):

        text = text.strip()

        if text.startswith(
            "```json"
        ):
            text = text[7:]

        elif text.startswith(
            "```"
        ):
            text = text[3:]

        if text.endswith(
            "```"
        ):
            text = text[:-3]

        return text.strip()