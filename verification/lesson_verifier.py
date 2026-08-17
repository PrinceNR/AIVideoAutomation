import re


class LessonVerifier:

    ALLOWED_DIFFICULTIES = {
        "Beginner",
        "Intermediate",
        "Advanced"
    }

    # Unicode ranges
    LANGUAGE_RANGES = {
        "malayalam": r"[\u0D00-\u0D7F]",
        "tamil": r"[\u0B80-\u0BFF]",
        "hindi": r"[\u0900-\u097F]"
    }

    def verify(self, lesson):

        results = []

        for word in lesson.words:
            result = self.verify_word(word)
            results.append(result)

        passed = sum(
            1 for item in results
            if item["status"] == "passed"
        )

        warnings = sum(
            1 for item in results
            if item["status"] == "warning"
        )

        errors = sum(
            1 for item in results
            if item["status"] == "error"
        )

        return {
            "topic": lesson.topic,
            "suggestions": getattr(
                lesson,
                "suggestions",
                ""
            ),
            "summary": {
                "total_words": len(results),
                "passed": passed,
                "warnings": warnings,
                "errors": errors
            },
            "results": results
        }

    def verify_word(self, word):

        issues = []

        self._check_basic_fields(word, issues)
        self._check_meaning(word, issues)
        self._check_difficulty(word, issues)
        self._check_pronunciation(word, issues)
        self._check_translations(word, issues)
        self._check_sentences(word, issues)
        self._check_verb_forms(word, issues)
        self._check_synonyms(word, issues)
        self._check_antonyms(word, issues)
        self._check_images(word, issues)

        has_error = any(
            issue["level"] == "error"
            for issue in issues
        )

        has_warning = any(
            issue["level"] == "warning"
            for issue in issues
        )

        if has_error:
            status = "error"
        elif has_warning:
            status = "warning"
        else:
            status = "passed"

        return {
            "word": word.word,
            "status": status,
            "issues": issues
        }

    # -------------------------------------------------
    # BASIC
    # -------------------------------------------------

    def _check_basic_fields(self, word, issues):

        required_fields = [
            "word",
            "meaning",
            "pronunciation",
            "part_of_speech",
            "difficulty"
        ]

        for field in required_fields:

            value = getattr(
                word,
                field,
                None
            )

            if not value:
                self._add_issue(
                    issues,
                    "error",
                    field,
                    f"{field} is empty."
                )

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

        if not current or not suggested:
            return False

        if not isinstance(current, str):
            return False

        if not isinstance(suggested, str):
            return False

        current_normalized = (
            current.strip().lower()
        )

        suggested_normalized = (
            suggested.strip().lower()
        )

        # Exact same proposed correction
        if (
            current_normalized
            == suggested_normalized
        ):
            return True

        # Particularly useful for IPA cases such as:
        #
        # current:
        # /abc/
        #
        # suggested:
        # /abc/ or /xyz/
        #
        if (
            issue.get("field")
            == "pronunciation"
            and current_normalized
            in suggested_normalized
        ):
            return True

        return False

    # -------------------------------------------------
    # MEANING
    # -------------------------------------------------

    def _check_meaning(self, word, issues):

        meaning = getattr(
            word,
            "meaning",
            ""
        )

        if not meaning:
            return

        count = self._word_count(
            meaning
        )

        if count > 15:
            self._add_issue(
                issues,
                "warning",
                "meaning",
                (
                    f"Meaning contains {count} words. "
                    "Maximum allowed is 15."
                )
            )

    # -------------------------------------------------
    # DIFFICULTY
    # -------------------------------------------------

    def _check_difficulty(self, word, issues):

        difficulty = getattr(
            word,
            "difficulty",
            ""
        )

        if difficulty not in self.ALLOWED_DIFFICULTIES:

            self._add_issue(
                issues,
                "error",
                "difficulty",
                (
                    f"Invalid difficulty: "
                    f"{difficulty}"
                )
            )

    # -------------------------------------------------
    # PRONUNCIATION
    # -------------------------------------------------

    def _check_pronunciation(self, word, issues):

        pronunciation = getattr(
            word,
            "pronunciation",
            ""
        )

        if not pronunciation:
            return

        if not (
            pronunciation.startswith("/")
            and pronunciation.endswith("/")
        ):
            self._add_issue(
                issues,
                "warning",
                "pronunciation",
                "Pronunciation may not be valid IPA format."
            )

    # -------------------------------------------------
    # TRANSLATIONS
    # -------------------------------------------------

    def _check_translations(self, word, issues):

        translations = getattr(
            word,
            "translations",
            {}
        )

        if not translations:
            self._add_issue(
                issues,
                "error",
                "translations",
                "Translations are missing."
            )
            return

        for language, pattern in self.LANGUAGE_RANGES.items():

            value = self._get_translation(
                translations,
                language
            )

            if not value:

                self._add_issue(
                    issues,
                    "error",
                    f"translations.{language}",
                    f"{language} translation is empty."
                )

                continue

            if not re.search(pattern, value):

                self._add_issue(
                    issues,
                    "error",
                    f"translations.{language}",
                    (
                        f"{language} translation does not "
                        "contain expected script characters."
                    )
                )

    # -------------------------------------------------
    # SENTENCES
    # -------------------------------------------------

    def _check_sentences(self, word, issues):

        sentence_fields = [
            "present_sentence",
            "past_sentence",
            "future_sentence"
        ]

        for field in sentence_fields:

            sentence = getattr(
                word,
                field,
                ""
            )

            if not sentence:

                self._add_issue(
                    issues,
                    "error",
                    field,
                    f"{field} is empty."
                )

                continue

            count = self._word_count(
                sentence
            )

            if count < 7 or count > 15:

                self._add_issue(
                    issues,
                    "warning",
                    field,
                    (
                        f"Sentence contains {count} words. "
                        "Expected 7 to 15 words."
                    )
                )

        self._check_sentence_word_usage(
            word,
            issues
        )

    def _check_sentence_word_usage(
        self,
        word,
        issues
    ):

        target = word.word.lower().strip()

        part_of_speech = (
            word.part_of_speech
            .lower()
            .strip()
        )

        if part_of_speech == "verb":

            present_forms = [
                target,
                getattr(
                    word,
                    "base_form",
                    ""
                ),
                getattr(
                    word,
                    "present_form",
                    ""
                )
            ]

            past_forms = [
                getattr(
                    word,
                    "past_form",
                    ""
                )
            ]

            future_forms = [
                target,
                getattr(
                    word,
                    "base_form",
                    ""
                )
            ]

            if not self._contains_any(
                word.present_sentence,
                present_forms
            ):
                self._add_issue(
                    issues,
                    "warning",
                    "present_sentence",
                    (
                        "Present sentence may not contain "
                        "the target verb."
                    )
                )

            if not self._contains_any(
                word.past_sentence,
                past_forms
            ):
                self._add_issue(
                    issues,
                    "warning",
                    "past_sentence",
                    (
                        "Past sentence may not contain "
                        "the correct past form."
                    )
                )

            if not self._contains_any(
                word.future_sentence,
                future_forms
            ):
                self._add_issue(
                    issues,
                    "warning",
                    "future_sentence",
                    (
                        "Future sentence may not contain "
                        "the target verb."
                    )
                )

            if "will" not in (
                word.future_sentence.lower()
            ):
                self._add_issue(
                    issues,
                    "warning",
                    "future_sentence",
                    (
                        "Future sentence does not contain "
                        "'will'."
                    )
                )

        else:

            for field in [
                "present_sentence",
                "past_sentence",
                "future_sentence"
            ]:

                sentence = getattr(
                    word,
                    field,
                    ""
                )

                if not self._contains_any(
                    sentence,
                    [target]
                ):
                    self._add_issue(
                        issues,
                        "warning",
                        field,
                        (
                            "Sentence may not contain "
                            "the vocabulary word."
                        )
                    )

    # -------------------------------------------------
    # VERB FORMS
    # -------------------------------------------------

    def _check_verb_forms(self, word, issues):

        part_of_speech = (
            getattr(
                word,
                "part_of_speech",
                ""
            )
            .lower()
            .strip()
        )

        fields = [
            "base_form",
            "present_form",
            "past_form"
        ]

        if part_of_speech == "verb":

            for field in fields:

                value = getattr(
                    word,
                    field,
                    ""
                )

                if not value:
                    self._add_issue(
                        issues,
                        "error",
                        field,
                        (
                            f"{field} is required "
                            "for verbs."
                        )
                    )

        else:

            for field in fields:

                value = getattr(
                    word,
                    field,
                    ""
                )

                if value:
                    self._add_issue(
                        issues,
                        "warning",
                        field,
                        (
                            f"{field} should normally "
                            "be empty for non-verbs."
                        )
                    )

    # -------------------------------------------------
    # SYNONYMS
    # -------------------------------------------------

    def _check_synonyms(self, word, issues):

        synonyms = getattr(
            word,
            "synonyms",
            []
        )

        if len(synonyms) < 3:

            self._add_issue(
                issues,
                "warning",
                "synonyms",
                (
                    f"Only {len(synonyms)} synonyms found. "
                    "Expected 3 to 5."
                )
            )

        if len(synonyms) > 5:

            self._add_issue(
                issues,
                "warning",
                "synonyms",
                (
                    f"{len(synonyms)} synonyms found. "
                    "Maximum expected is 5."
                )
            )

    # -------------------------------------------------
    # ANTONYMS
    # -------------------------------------------------

    def _check_antonyms(self, word, issues):

        antonyms = getattr(
            word,
            "antonyms",
            []
        )

        # Empty is allowed because some words
        # do not have a natural antonym.
        if antonyms and len(antonyms) < 2:

            self._add_issue(
                issues,
                "warning",
                "antonyms",
                (
                    "If antonyms are provided, "
                    "prefer at least 2."
                )
            )

        if len(antonyms) > 5:

            self._add_issue(
                issues,
                "warning",
                "antonyms",
                (
                    f"{len(antonyms)} antonyms found. "
                    "Maximum expected is 5."
                )
            )

    # -------------------------------------------------
    # IMAGES
    # -------------------------------------------------

    def _check_images(self, word, issues):

        keywords = getattr(
            word,
            "image_keywords",
            []
        )

        search_query = getattr(
            word,
            "search_query",
            ""
        )

        if len(keywords) < 3:

            self._add_issue(
                issues,
                "warning",
                "image_keywords",
                (
                    f"Only {len(keywords)} image keywords. "
                    "Expected 3 to 5."
                )
            )

        if len(keywords) > 5:

            self._add_issue(
                issues,
                "warning",
                "image_keywords",
                (
                    f"{len(keywords)} image keywords. "
                    "Maximum expected is 5."
                )
            )

        if not search_query:

            self._add_issue(
                issues,
                "error",
                "search_query",
                "Image search query is empty."
            )

        elif (
            search_query.lower().strip()
            == word.word.lower().strip()
        ):

            self._add_issue(
                issues,
                "warning",
                "search_query",
                (
                    "Search query only repeats "
                    "the vocabulary word."
                )
            )

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------

    def _get_translation(
        self,
        translations,
        language
    ):

        if isinstance(
            translations,
            dict
        ):
            return translations.get(
                language,
                ""
            )

        return getattr(
            translations,
            language,
            ""
        )

    def _word_count(self, text):

        return len(
            re.findall(
                r"\b[\w'-]+\b",
                text,
                flags=re.UNICODE
            )
        )

    def _contains_any(
        self,
        sentence,
        forms
    ):

        sentence = sentence.lower()

        for form in forms:

            if not form:
                continue

            form = form.lower().strip()

            pattern = (
                r"(?<!\w)"
                + re.escape(form)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                sentence
            ):
                return True

        return False

    def _add_issue(
        self,
        issues,
        level,
        field,
        message
    ):

        issues.append({
            "level": level,
            "field": field,
            "message": message
        })