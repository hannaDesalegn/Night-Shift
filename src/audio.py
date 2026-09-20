"""Procedurally synthesised sound effects.

Every sound is generated from simple waveforms at start-up, so the game ships without
audio assets. If the mixer cannot be opened (no device, headless machine) the game
carries on silently.
"""

import array
import functools
import math
import random

import pygame

from src import settings

SAMPLE_RATE = 22050
AMPLITUDE = 22000


def _envelope(count, attack, release):
    """Attack/release gain curve for a whole voice."""
    attack_samples = max(1, int(count * attack))
    release_samples = max(1, int(count * release))
    gains = []
    for i in range(count):
        if i < attack_samples:
            gains.append(i / attack_samples)
        elif i > count - release_samples:
            gains.append(max(0.0, (count - i) / release_samples))
        else:
            gains.append(1.0)
    return gains


def _phases(freq, end_freq, count):
    step = math.tau / SAMPLE_RATE
    phases = []
    phase = 0.0
    delta = (end_freq - freq) / count if count else 0.0
    current = freq
    for _ in range(count):
        phases.append(phase)
        phase += step * current
        current += delta
    return phases


def tone(
    freq, duration, shape="sine", volume=0.5, attack=0.02, release=0.35, end_freq=None, seed=1
):
    """One voice: constant or gliding pitch with an attack/release envelope.

    Written as whole-list passes rather than a per-sample function call; synthesising the
    whole library happens at start-up and the naive version was noticeably slow.
    """
    count = int(SAMPLE_RATE * duration)
    phases = _phases(freq, freq if end_freq is None else end_freq, count)
    sin = math.sin
    if shape == "sine":
        wave = [sin(p) for p in phases]
    elif shape == "square":
        wave = [1.0 if sin(p) >= 0 else -1.0 for p in phases]
    elif shape == "saw":
        wave = [2 * ((p / math.tau) % 1.0) - 1 for p in phases]
    else:
        rng = random.Random(seed)
        wave = [rng.uniform(-1, 1) for _ in phases]
    gains = _envelope(count, attack, release)
    scale = AMPLITUDE * volume
    return array.array("h", (int(w * g * scale) for w, g in zip(wave, gains, strict=True)))


def mix(*voices):
    """Overlay voices, clipping the sum to the sample range."""
    length = max(len(v) for v in voices)
    out = [0] * length
    for voice in voices:
        for i, sample in enumerate(voice):
            out[i] += sample
    limit = AMPLITUDE
    return array.array("h", (max(-limit, min(limit, value)) for value in out))


def sequence(*voices):
    out = array.array("h")
    for voice in voices:
        out.extend(voice)
    return out


# One process only ever needs one copy of the samples.
@functools.lru_cache(maxsize=1)
def _library():
    """Name -> samples. Kept declarative so sounds are easy to retune."""
    return {
        "pickup": sequence(
            tone(880, 0.09, volume=0.35, release=0.5),
            tone(1320, 0.16, volume=0.3, release=0.7),
        ),
        "battery": sequence(tone(520, 0.08, volume=0.35), tone(780, 0.14, volume=0.3, release=0.7)),
        "door_open": mix(
            tone(70, 0.55, shape="sine", volume=0.4, end_freq=48),
            tone(240, 0.5, shape="noise", volume=0.12, attack=0.2, release=0.6),
        ),
        "door_locked": mix(
            tone(120, 0.22, shape="square", volume=0.28, attack=0.01, release=0.2),
            tone(60, 0.22, shape="square", volume=0.2),
        ),
        "generator_start": tone(80, 0.9, shape="saw", volume=0.3, end_freq=210, release=0.2),
        "power_on": mix(
            tone(220, 1.0, volume=0.28, attack=0.25, release=0.4),
            tone(330, 1.0, volume=0.22, attack=0.3, release=0.4),
            tone(440, 1.0, volume=0.18, attack=0.35, release=0.4),
        ),
        "damage": mix(
            tone(200, 0.35, shape="square", volume=0.3, end_freq=70, attack=0.005),
            tone(400, 0.25, shape="noise", volume=0.25, attack=0.005, release=0.8),
        ),
        "click": tone(1200, 0.035, shape="square", volume=0.18, attack=0.05, release=0.6),
        "empty": sequence(
            tone(300, 0.12, shape="square", volume=0.2),
            tone(180, 0.22, shape="square", volume=0.18, end_freq=120),
        ),
        "spotted": mix(
            tone(300, 0.7, shape="square", volume=0.22, attack=0.01, release=0.5),
            tone(317, 0.7, shape="square", volume=0.22, attack=0.01, release=0.5),
        ),
        "escape": sequence(
            tone(440, 0.12, volume=0.3),
            tone(554, 0.12, volume=0.3),
            tone(659, 0.12, volume=0.3),
            tone(880, 0.4, volume=0.3, release=0.6),
        ),
        "hum": mix(
            tone(55, 2.0, volume=0.16, attack=0.2, release=0.2),
            tone(110, 2.0, volume=0.05, attack=0.3, release=0.3),
        ),
    }


class Audio:
    """Loads the sound library if a mixer is available; otherwise every call is a no-op."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self.ambient_channel = None
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        except pygame.error as error:
            print(f"Audio disabled: {error}")
            return
        self.sounds = {name: pygame.mixer.Sound(buffer=data) for name, data in _library().items()}
        for sound in self.sounds.values():
            sound.set_volume(settings.MASTER_VOLUME)
        self.enabled = True

    def play(self, name, volume=1.0):
        if not self.enabled:
            return
        sound = self.sounds[name]
        sound.set_volume(settings.MASTER_VOLUME * volume)
        sound.play()

    def start_ambience(self):
        if not self.enabled:
            return
        self.ambient_channel = self.sounds["hum"].play(loops=-1)
        if self.ambient_channel:
            self.ambient_channel.set_volume(settings.AMBIENT_VOLUME)

    def stop_ambience(self):
        if self.ambient_channel:
            self.ambient_channel.stop()
            self.ambient_channel = None

    def shutdown(self):
        if self.enabled:
            pygame.mixer.quit()
            self.enabled = False
