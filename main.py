import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from src.game import Game  # noqa: E402


def main():
    Game().run()


if __name__ == "__main__":
    main()
