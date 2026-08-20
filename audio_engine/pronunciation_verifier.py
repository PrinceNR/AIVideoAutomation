from pathlib import Path
import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk


load_dotenv()


class PronunciationVerifier:

    def __init__(
        self,
        min_score: float = 85.0
    ):

        self.api_key = os.getenv(
            "AZURE_SPEECH_KEY"
        )

        self.region = os.getenv(
            "AZURE_SPEECH_REGION"
        )

        self.min_score = min_score

        if not self.api_key:
            raise ValueError(
                "AZURE_SPEECH_KEY not found in .env"
            )

        if not self.region:
            raise ValueError(
                "AZURE_SPEECH_REGION not found in .env"
            )

    def verify(
        self,
        word: str,
        audio_path: Path
    ) -> dict:

        audio_path = Path(
            audio_path
        )

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        speech_config = speechsdk.SpeechConfig(
            subscription=self.api_key,
            region=self.region
        )

        audio_config = speechsdk.audio.AudioConfig(
            filename=str(audio_path)
        )

        pronunciation_config = (
            speechsdk.PronunciationAssessmentConfig(
                reference_text=word,
                grading_system=(
                    speechsdk
                    .PronunciationAssessmentGradingSystem
                    .HundredMark
                ),
                granularity=(
                    speechsdk
                    .PronunciationAssessmentGranularity
                    .Phoneme
                ),
                enable_miscue=True
            )
        )

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            language="en-IN",
            audio_config=audio_config
        )

        pronunciation_config.apply_to(
            recognizer
        )

        result = recognizer.recognize_once()

        if (
            result.reason
            == speechsdk.ResultReason.RecognizedSpeech
        ):

            assessment = (
                speechsdk
                .PronunciationAssessmentResult(
                    result
                )
            )

            recognized = (
                result.text
                .strip()
                .rstrip(".")
                .lower()
            )

            expected = (
                word
                .strip()
                .lower()
            )

            accuracy = float(
                assessment.accuracy_score
            )

            phoneme_scores = []

            for word_result in assessment.words:

                for phoneme in word_result.phonemes:

                    phoneme_scores.append(
                        {
                            "phoneme": phoneme.phoneme,
                            "accuracy": float(
                                phoneme.accuracy_score
                            )
                        }
                    )

            passed = (
                recognized == expected
                and accuracy >= self.min_score
            )

            return {
                "word": word,
                "recognized": recognized,
                "accuracy": accuracy,
                "pronunciation_score": float(
                    assessment.pronunciation_score
                ),
                "completeness": float(
                    assessment.completeness_score
                ),
                "fluency": float(
                    assessment.fluency_score
                ),
                "phonemes": phoneme_scores,
                "passed": passed
            }

        if (
            result.reason
            == speechsdk.ResultReason.NoMatch
        ):

            return {
                "word": word,
                "recognized": None,
                "accuracy": 0.0,
                "phonemes": [],
                "passed": False,
                "error": "No speech recognized"
            }

        if (
            result.reason
            == speechsdk.ResultReason.Canceled
        ):

            cancellation = (
                speechsdk.CancellationDetails(
                    result
                )
            )

            return {
                "word": word,
                "recognized": None,
                "accuracy": 0.0,
                "phonemes": [],
                "passed": False,
                "error": (
                    cancellation.error_details
                    or str(cancellation.reason)
                )
            }

        return {
            "word": word,
            "recognized": None,
            "accuracy": 0.0,
            "phonemes": [],
            "passed": False,
            "error": (
                f"Unexpected result: "
                f"{result.reason}"
            )
        }