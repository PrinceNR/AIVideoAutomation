from presentation.audio_duration_calculator import AudioDurationCalculator


calculator = AudioDurationCalculator()

duration = calculator.get_duration(
    "output/farming/audio/cultivate/pronunciation.mp3"
)

print(duration)