import json
import unittest

from image_engine.image_search_strategy import (
    ImageSearchStrategy
)
from media_engine.batch_media_planner import (
    BatchMediaPlanner
)
from media_engine.media_plan_applier import (
    MediaPlanApplier
)
from models.word import Word


def make_word(
    word,
    meaning,
    part_of_speech,
    present_sentence,
    past_sentence,
    future_sentence
):
    return Word(
        word=word,
        meaning=meaning,
        pronunciation=f"/{word}/",
        part_of_speech=part_of_speech,
        difficulty="Intermediate",
        translations={"hindi": "test"},
        present_sentence=present_sentence,
        past_sentence=past_sentence,
        future_sentence=future_sentence,
        base_form=word,
        present_form=word,
        past_form=word,
        synonyms=["existing synonym"],
        antonyms=["existing antonym"],
        image_keywords=["old keyword"],
        search_query="old query"
    )


class VisualQueryPlanningTests(unittest.TestCase):

    def setUp(self):
        self.words = [
            make_word(
                "rescue",
                "to save someone from danger",
                "verb",
                "The lifeguard rescues the swimmer.",
                "The firefighter rescued the child.",
                "They will rescue the stranded hiker."
            ),
            make_word(
                "reliable",
                (
                    "can be trusted to work well "
                    "or behave consistently"
                ),
                "adjective",
                "The reliable employee finishes work on time.",
                "She was reliable during the project.",
                "He will be reliable at his new job."
            ),
            make_word(
                "reputation",
                (
                    "the opinion people have formed about a "
                    "person or organization over time"
                ),
                "noun",
                "Customers read reviews of the business.",
                "The company earned a good reputation.",
                "Positive reviews will improve its reputation."
            )
        ]

        raw_plans = {
            "plans": [
                {
                    "index": 0,
                    "preferred_type": "video",
                    "requires_motion": True,
                    "reason": "The rescue action benefits from motion.",
                    "visual_concept": (
                        "a lifeguard pulling a swimmer from danger"
                    ),
                    "image_search_queries": [
                        "lifeguard rescuing swimmer",
                        "firefighter carrying person safety",
                        "water rescue action"
                    ]
                },
                {
                    "index": 1,
                    "preferred_type": "photo",
                    "requires_motion": False,
                    "reason": (
                        "A workplace scenario shows consistent behavior."
                    ),
                    "visual_concept": (
                        "an employee consistently completing work "
                        "correctly and on time"
                    ),
                    "image_search_queries": [
                        "employee completing task on time",
                        "worker meeting project deadline",
                        "professional checking finished work"
                    ]
                },
                {
                    "index": 2,
                    "preferred_type": "illustration",
                    "requires_motion": False,
                    "reason": (
                        "Reviews make accumulated public opinion visible."
                    ),
                    "visual_concept": (
                        "customers reading and discussing accumulated "
                        "business reviews"
                    ),
                    "image_search_queries": [
                        "customer reading business reviews",
                        "people discussing company reviews",
                        "business owner checking ratings"
                    ]
                }
            ]
        }

        self.plans = BatchMediaPlanner()._parse(
            json.dumps(raw_plans),
            expected_count=3
        )
        MediaPlanApplier().apply(
            self.words,
            self.plans
        )
        self.strategy = ImageSearchStrategy()

    def test_concrete_action_verb_gets_action_queries(self):
        queries = self.strategy.build_queries(
            self.words[0]
        )

        self.assertEqual(
            queries,
            [
                "lifeguard rescuing swimmer",
                "firefighter carrying person safety",
                "water rescue action"
            ]
        )

    def test_abstract_adjective_gets_scenario_queries(self):
        queries = self.strategy.build_queries(
            self.words[1]
        )

        self.assertEqual(len(queries), 3)
        self.assertTrue(
            all(
                "reliable" not in query.lower()
                for query in queries
            )
        )
        self.assertIn(
            "employee completing task on time",
            queries
        )
        self.assertIn(
            "worker meeting project deadline",
            queries
        )

    def test_abstract_noun_gets_teachable_scenario(self):
        queries = self.strategy.build_queries(
            self.words[2]
        )

        self.assertEqual(len(queries), 3)
        self.assertTrue(
            any("reviews" in query for query in queries)
        )
        self.assertNotIn(
            "successful business award",
            queries
        )
        self.assertNotIn(
            "professional handshake",
            queries
        )

    def test_queries_are_short_and_search_friendly(self):
        for word in self.words:
            queries = self.strategy.build_queries(word)

            self.assertEqual(len(queries), 3)

            for query in queries:
                self.assertGreaterEqual(
                    len(query.split()),
                    2
                )
                self.assertLessEqual(
                    len(query.split()),
                    6
                )

    def test_existing_word_fields_survive_query_planning(self):
        reliable = self.words[1]

        self.assertEqual(
            reliable.meaning,
            (
                "can be trusted to work well "
                "or behave consistently"
            )
        )
        self.assertEqual(
            reliable.part_of_speech,
            "adjective"
        )
        self.assertEqual(
            reliable.present_sentence,
            "The reliable employee finishes work on time."
        )
        self.assertEqual(
            reliable.past_sentence,
            "She was reliable during the project."
        )
        self.assertEqual(
            reliable.future_sentence,
            "He will be reliable at his new job."
        )
        self.assertEqual(
            reliable.translations,
            {"hindi": "test"}
        )
        self.assertEqual(
            reliable.synonyms,
            ["existing synonym"]
        )
        self.assertEqual(
            reliable.antonyms,
            ["existing antonym"]
        )

    def test_prompt_uses_full_teaching_context(self):
        reliable = self.words[1]
        reliable.preferred_media = "photo"
        reliable.media_reason = (
            "A workplace scenario demonstrates consistency."
        )
        reliable.requires_motion = False

        prompt = BatchMediaPlanner()._build_prompt(
            [reliable]
        )

        self.assertIn(reliable.meaning, prompt)
        self.assertIn(reliable.part_of_speech, prompt)
        self.assertIn(reliable.present_sentence, prompt)
        self.assertIn(reliable.past_sentence, prompt)
        self.assertIn(reliable.future_sentence, prompt)
        self.assertIn(reliable.media_reason, prompt)
        self.assertIn('"existing_preferred_media": "photo"', prompt)
        self.assertIn('"existing_requires_motion": false', prompt)
        self.assertIn("VISUAL TEACHING CONCEPT", prompt)


if __name__ == "__main__":
    unittest.main()
