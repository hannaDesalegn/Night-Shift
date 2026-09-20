import os

# Run pygame headless so the suite works in CI and over SSH.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


import pygame  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def display():
    """Surfaces are converted to the display format, so one must exist even headless."""
    pygame.init()
    pygame.display.set_mode((320, 240))
    yield
    pygame.quit()
