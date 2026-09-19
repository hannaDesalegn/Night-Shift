"""Fonts, menus and full-screen UI overlays."""

import math

import pygame

from src import controls, settings

CONTROLS_HELP = (
    ("WASD / Arrows", "Move"),
    ("E", "Interact"),
    ("F", "Toggle flashlight"),
    ("Esc / P", "Pause"),
    ("R", "Restart (paused or run over)"),
)


class Fonts:
    def __init__(self):
        self.title = self._make(92, bold=True)
        self.heading = self._make(44, bold=True)
        self.body = self._make(24)
        self.small = self._make(18)
        self.label = self._make(15, bold=True)
        self.stencil = self._make(44, bold=True)

    @staticmethod
    def _make(size, bold=False):
        return pygame.font.SysFont(settings.FONT_NAMES, size, bold=bold)


def glowing_text(font, text, color, glow_color, radius=10):
    """Text over a soft halo, made by down- and up-scaling a copy (built once, then cached)."""
    base = font.render(text, True, color)
    w, h = base.get_size()
    pad = radius * 2
    halo = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    halo.blit(font.render(text, True, glow_color), (pad, pad))
    small = pygame.transform.smoothscale(
        halo, (max(1, halo.get_width() // 6), max(1, halo.get_height() // 6))
    )
    halo = pygame.transform.smoothscale(small, halo.get_size())
    halo.blit(base, (pad, pad))
    return halo


def draw_centered(surface, font, text, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))
    return image.get_rect(center=center)


class Menu:
    """Vertical list of options driven by keyboard or mouse."""

    def __init__(self, options):
        self.options = options
        self.index = 0
        self.rects = []

    def reset(self):
        self.index = 0

    def handle(self, event):
        """Returns the chosen option key, or None."""
        if event.type == pygame.KEYDOWN:
            if event.key in controls.MOVE_UP:
                self.index = (self.index - 1) % len(self.options)
            elif event.key in controls.MOVE_DOWN:
                self.index = (self.index + 1) % len(self.options)
            elif event.key in controls.CONFIRM:
                return self.options[self.index][0]
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self.index = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self.index = i
                    return self.options[i][0]
        return None

    def draw(self, surface, fonts, center_x, top, t):
        self.rects = []
        for i, (_, label) in enumerate(self.options):
            y = top + i * 52
            selected = i == self.index
            rect = pygame.Rect(0, 0, 320, 44)
            rect.center = (center_x, y)
            if selected:
                pulse = 0.5 + 0.5 * math.sin(t * 4)
                bar = pygame.Surface(rect.size, pygame.SRCALPHA)
                bar.fill((*settings.ACCENT, int(26 + 20 * pulse)))
                surface.blit(bar, rect)
                pygame.draw.rect(surface, settings.ACCENT, rect, 1)
                marker = (rect.x + 16, rect.centery)
                pygame.draw.polygon(
                    surface,
                    settings.ACCENT,
                    [
                        (marker[0], marker[1] - 6),
                        (marker[0] + 8, marker[1]),
                        (marker[0], marker[1] + 6),
                    ],
                )
            color = settings.ACCENT if selected else settings.TEXT_DIM
            draw_centered(surface, fonts.body, label.upper(), color, rect.center)
            self.rects.append(rect)


class Screens:
    """Draws the non-gameplay screens; owns cached surfaces so they are built once."""

    def __init__(self, fonts, size):
        self.fonts = fonts
        self.size = size
        self.title = glowing_text(
            fonts.title, settings.TITLE.upper(), (236, 226, 206), settings.ACCENT, 14
        )
        self.shade = pygame.Surface(size, pygame.SRCALPHA)
        self.shade.fill((4, 5, 10, 160))
        self.vignette = _vignette(size)

    def dim(self, surface):
        surface.blit(self.shade, (0, 0))

    def draw_menu(self, surface, menu, t, show_controls):
        width, height = self.size
        surface.blit(self.vignette, (0, 0))
        # Faint electrical flicker on the title.
        flicker = 255 if math.sin(t * 13) + math.sin(t * 7.3) < 1.7 else 150
        self.title.set_alpha(flicker)
        surface.blit(self.title, self.title.get_rect(center=(width / 2, height * 0.26)))
        tagline = "Restore the power. Find the exit. Don't let it see you."
        draw_centered(
            surface, self.fonts.small, tagline, settings.TEXT_DIM, (width / 2, height * 0.37)
        )
        if show_controls:
            self.draw_controls(surface, (width / 2, height * 0.64))
        else:
            menu.draw(surface, self.fonts, width / 2, height * 0.52, t)
        hint = "Esc to go back" if show_controls else "W/S or arrows to choose  ·  Enter to select"
        draw_centered(surface, self.fonts.small, hint, (80, 86, 100), (width / 2, height - 36))

    def draw_controls(self, surface, center):
        panel = pygame.Rect(0, 0, 460, 60 + 38 * len(CONTROLS_HELP))
        panel.center = center
        pygame.draw.rect(surface, (14, 16, 24), panel, border_radius=6)
        pygame.draw.rect(surface, (60, 66, 84), panel, 1, border_radius=6)
        heading = self.fonts.label.render("CONTROLS", True, settings.ACCENT)
        surface.blit(heading, (panel.x + 24, panel.y + 18))
        for i, (keys, action) in enumerate(CONTROLS_HELP):
            y = panel.y + 52 + i * 38
            surface.blit(self.fonts.body.render(keys, True, settings.TEXT_COLOR), (panel.x + 24, y))
            label = self.fonts.body.render(action, True, settings.TEXT_DIM)
            surface.blit(label, label.get_rect(topright=(panel.right - 24, y)))


def _vignette(size):
    """Darkened edges, drawn as concentric rectangles with rising alpha."""
    width, height = size
    surface = pygame.Surface(size, pygame.SRCALPHA)
    steps = 24
    for i in range(steps):
        inset = int(i * min(width, height) / (steps * 3.2))
        alpha = int(150 * (1 - i / steps) ** 2)
        pygame.draw.rect(
            surface, (0, 0, 0, alpha), (inset, inset, width - 2 * inset, height - 2 * inset), 12
        )
    return surface
