import pygame

from src.audio import SAMPLE_RATE, Audio, mix, sequence, tone


def test_tone_length_matches_duration():
    samples = tone(440, 0.1)
    assert len(samples) == int(SAMPLE_RATE * 0.1)


def test_tone_stays_inside_16_bit_range():
    assert all(-32768 <= s <= 32767 for s in tone(220, 0.05, shape="saw", volume=1.0))


def test_mix_and_sequence_lengths():
    a, b = tone(440, 0.05), tone(880, 0.1)
    assert len(mix(a, b)) == len(b)
    assert len(sequence(a, b)) == len(a) + len(b)


def test_audio_loads_every_sound_or_disables_itself():
    pygame.init()
    audio = Audio()
    if audio.enabled:
        assert "pickup" in audio.sounds
        audio.play("pickup")
    else:
        # Playing without a mixer must stay harmless.
        audio.play("pickup")
    audio.shutdown()
