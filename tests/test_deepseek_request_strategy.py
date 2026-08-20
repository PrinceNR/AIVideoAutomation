import json
import unittest
from types import SimpleNamespace

from verification.deepseek_client import DeepSeekClient
from verification.semantic_lesson_verifier import (
    SemanticLessonVerifier
)


class FakeCompletions:

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def make_response(
    content,
    finish_reason="stop"
):
    return SimpleNamespace(
        model="deepseek-v4-flash",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content
                ),
                finish_reason=finish_reason
            )
        ]
    )


def make_client(responses):
    completions = FakeCompletions(responses)
    deepseek = DeepSeekClient.__new__(
        DeepSeekClient
    )
    deepseek.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=completions
        )
    )
    deepseek.last_model_used = None
    return deepseek, completions


def make_lesson():
    return {
        "title": "Test lesson",
        "topic": "test",
        "suggestions": "",
        "words": [{
            "word": "test",
            "meaning": "to examine something",
            "pronunciation": "/test/",
            "part_of_speech": "verb",
            "difficulty": "Beginner",
            "translations": {
                "malayalam": "പരിശോധിക്കുക",
                "tamil": "சோதிக்க",
                "hindi": "जाँचना"
            },
            "present_sentence": "I test the device.",
            "past_sentence": "I tested the device.",
            "future_sentence": "I will test the device.",
            "base_form": "test",
            "present_form": "tests",
            "past_form": "tested",
            "synonyms": ["examine"],
            "antonyms": [],
            "image_keywords": ["person testing device"],
            "search_query": "testing device"
        }]
    }


def make_valid_report(lesson):
    return {
        "overall_status": "passed",
        "summary": {
            "total_words": 1,
            "passed": 1,
            "warnings": 0,
            "errors": 0
        },
        "results": [{
            "word": "test",
            "status": "passed",
            "issues": []
        }],
        "corrected_lesson": lesson
    }


class DeepSeekRequestStrategyTests(unittest.TestCase):

    def test_primary_success_uses_one_non_thinking_call(self):
        client, completions = make_client([
            make_response('{"result": "ok"}')
        ])

        result = client.generate("verify")

        self.assertEqual(
            json.loads(result),
            {"result": "ok"}
        )
        self.assertEqual(len(completions.calls), 1)

        request = completions.calls[0]
        self.assertEqual(
            request["response_format"],
            {"type": "json_object"}
        )
        self.assertEqual(
            request["extra_body"]["thinking"]["type"],
            "disabled"
        )
        self.assertNotIn("reasoning_effort", request)

    def test_length_limited_primary_uses_valid_fallback(self):
        lesson = make_lesson()
        valid_fallback = json.dumps(
            make_valid_report(lesson),
            ensure_ascii=False
        )
        client, completions = make_client([
            make_response("", finish_reason="length"),
            make_response(valid_fallback)
        ])
        verifier = SemanticLessonVerifier.__new__(
            SemanticLessonVerifier
        )
        verifier.client = client

        report = verifier.verify(lesson)

        self.assertEqual(len(completions.calls), 2)
        self.assertNotIn(
            "response_format",
            completions.calls[1]
        )
        self.assertEqual(
            completions.calls[1]["extra_body"]
            ["thinking"]["type"],
            "disabled"
        )
        self.assertEqual(
            report["overall_status"],
            "passed"
        )
        self.assertEqual(
            report["corrected_lesson"],
            lesson
        )

    def test_both_strategies_failing_returns_clean_failure(self):
        lesson = make_lesson()
        client, completions = make_client([
            make_response("", finish_reason="length"),
            make_response("{malformed", finish_reason="stop")
        ])
        verifier = SemanticLessonVerifier.__new__(
            SemanticLessonVerifier
        )
        verifier.client = client

        report = verifier.verify(lesson)

        self.assertEqual(len(completions.calls), 2)
        self.assertEqual(report["overall_status"], "error")
        self.assertEqual(report["summary"]["errors"], 1)
        self.assertIsNone(report["corrected_lesson"])
        self.assertIn(
            "both request strategies",
            report["verification_error"]
        )

    def test_incomplete_corrected_lesson_is_rejected(self):
        lesson = make_lesson()
        incomplete = make_valid_report(lesson)
        incomplete["corrected_lesson"] = {
            "title": "Test lesson",
            "topic": "test",
            "suggestions": "",
            "words": [{"word": "test"}]
        }
        client, completions = make_client([
            make_response(json.dumps(incomplete))
        ])
        verifier = SemanticLessonVerifier.__new__(
            SemanticLessonVerifier
        )
        verifier.client = client

        report = verifier.verify(lesson)

        self.assertEqual(len(completions.calls), 1)
        self.assertEqual(report["overall_status"], "error")
        self.assertIsNone(report["corrected_lesson"])
        self.assertIn(
            "incomplete corrected lesson",
            report["verification_error"]
        )


if __name__ == "__main__":
    unittest.main()
