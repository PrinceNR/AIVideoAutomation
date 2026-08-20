from pathlib import Path

from audio_engine.audio_converter import (
    AudioConverter
)

from audio_engine.pronunciation_generator import (
    PronunciationGenerator
)

from audio_engine.pronunciation_verifier import (
    PronunciationVerifier
)

from config import PRONUNCIATION_MIN_SCORE


class PronunciationService:

    def __init__(self):

        self.generator = (
            PronunciationGenerator()
        )

        self.verifier = (
            PronunciationVerifier(
                min_score=PRONUNCIATION_MIN_SCORE
            )
        )

        self.converter = (
            AudioConverter()
        )

    def generate_verified(
        self,
        word: str,
        output_path: Path
    ) -> dict:

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_wav_path = (
            output_path.parent
            / f"{output_path.stem}_verification.wav"
        )

        print(
            f"\nGenerating pronunciation: "
            f"{word}"
        )

        self.generator.generate(
            word=word,
            output_path=temp_wav_path
        )

        print(
            f"Verifying pronunciation: "
            f"{word}"
        )

        result = self.verifier.verify(
            word=word,
            audio_path=temp_wav_path
        )

        print(
            f"Pronunciation accuracy: "
            f"{result['accuracy']}"
        )

        if not result["passed"]:

            print(
                f"Pronunciation rejected: "
                f"{word}"
            )

            raise RuntimeError(
                f"Pronunciation verification "
                f"failed for '{word}'. "
                f"Accuracy: {result['accuracy']}"
            )

        print(
            f"Pronunciation accepted: "
            f"{word}"
        )

        self.converter.wav_to_mp3(
            input_path=temp_wav_path,
            output_path=output_path
        )

        temp_wav_path.unlink(
            missing_ok=True
        )

        print(
            f"Final pronunciation: "
            f"{output_path}"
        )

        return result