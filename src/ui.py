"""Fonts, HUD and menu screens."""

import pygame

from src import settings


class Fonts:
    def __init__(self):
        self.title = self._make(88, bold=True)
        self.heading = self._make(40, bold=True)
        self.body = self._make(24)
        self.small = self._make(18)
        self.stencil = self._make(44, bold=True)

    @staticmethod
    def _make(size, bold=False):
        return pygame.font.SysFont(settings.FONT_NAMES, size, bold=bold)
