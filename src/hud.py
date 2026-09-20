"""In-game heads-up display."""

import math

import pygame

from src import settings
from src.session import OBJECTIVES
from src.ui import draw_centered
from src.utils import clamp, format_time

PANEL_BG = (10, 12, 18, 190)
PANEL_EDGE = (62, 70, 88)
HEALTH_COLOR = (206, 72, 66)
ENERGY_COLOR = (238, 196, 92)
TOAST_TIME = 3.0
MAX_TOASTS = 3


def panel(surface, rect, radius=6):
    face = pygame.Surface(rect.size, pygame.SRCALPHA)
    face.fill((0, 0, 0, 0))
    pygame.draw.rect(face, PANEL_BG, face.get_rect(), border_radius=radius)
    surface.blit(face, rect)
    pygame.draw.rect(surface, PANEL_EDGE, rect, 1, border_radius=radius)


def segmented_bar(surface, rect, fraction, color, segments=10):
    pygame.draw.rect(surface, (16, 18, 24), rect, border_radius=2)
    gap = 3
    cell_w = (rect.width - gap * (segments - 1)) / segments
    filled = fraction * segments
    for i in range(segments):
        amount = clamp(filled - i, 0, 1)
        if amount <= 0:
            break
        cell = pygame.Rect(
            rect.x + i * (cell_w + gap), rect.y, max(1, cell_w * amount), rect.height
        )
        surface.fill(color, cell)
    pygame.draw.rect(surface, (58, 64, 78), rect, 1, border_radius=2)


class HUD:
    def __init__(self, fonts, size):
        self.fonts = fonts
        self.size = size
        self.toasts = []

    def notify(self, text):
        if not text:
            return
        self.toasts.append([text, TOAST_TIME])
        del self.toasts[:-MAX_TOASTS]

    def clear(self):
        self.toasts.clear()

    def update(self, dt):
        for toast in self.toasts:
            toast[1] -= dt
        self.toasts = [toast for toast in self.toasts if toast[1] > 0]

    def draw(self, surface, session, t):
        self._draw_status(surface, session, t)
        self._draw_clock(surface, session, t)
        self._draw_objective(surface, session)
        self._draw_prompt(surface, session)
        self._draw_toasts(surface)

    def _draw_status(self, surface, session, t):
        player = session.player
        box = pygame.Rect(24, 22, 260, 104)
        panel(surface, box)
        fonts = self.fonts

        low_health = player.health <= settings.PLAYER_MAX_HEALTH * 0.34
        pulse = 0.65 + 0.35 * math.sin(t * 6)
        health_color = HEALTH_COLOR if not low_health else [int(c * pulse) for c in (255, 90, 80)]
        surface.blit(
            fonts.label.render("HEALTH", True, settings.TEXT_DIM), (box.x + 16, box.y + 14)
        )
        health_rect = pygame.Rect(box.x + 16, box.y + 32, box.width - 32, 12)
        fraction = player.health / settings.PLAYER_MAX_HEALTH
        segmented_bar(surface, health_rect, fraction, health_color, segments=4)

        label = "FLASHLIGHT"
        color = ENERGY_COLOR
        if player.depleted:
            label, color = "FLASHLIGHT — DEAD", (120, 90, 60)
        elif player.flashlight_low:
            label = "FLASHLIGHT — LOW"
            color = ENERGY_COLOR if int(t * 5) % 2 else (140, 104, 48)
        surface.blit(fonts.label.render(label, True, settings.TEXT_DIM), (box.x + 16, box.y + 56))
        energy_rect = pygame.Rect(box.x + 16, box.y + 74, box.width - 32, 12)
        segmented_bar(surface, energy_rect, player.energy_fraction, color)

        self._draw_inventory(surface, session, pygame.Rect(box.x, box.bottom + 10, box.width, 26))

    def _draw_inventory(self, surface, session, rect):
        held = [item for item in ("keycard", "component") if session.player.has(item)]
        for i, item in enumerate(held):
            slot = pygame.Rect(rect.x + i * 132, rect.y, 124, 26)
            panel(surface, slot, radius=4)
            if item == "keycard":
                icon = pygame.Rect(slot.x + 10, slot.y + 8, 16, 11)
                pygame.draw.rect(surface, (236, 168, 60), icon, border_radius=2)
                pygame.draw.rect(surface, (60, 40, 20), (icon.x + 2, icon.y + 2, 12, 4))
                text = "KEYCARD"
            else:
                icon = pygame.Rect(slot.x + 13, slot.y + 5, 10, 16)
                pygame.draw.rect(surface, (80, 220, 230), icon, border_radius=2)
                text = "FUSE CELL"
            label = self.fonts.label.render(text, True, settings.TEXT_COLOR)
            surface.blit(label, (slot.x + 36, slot.y + 8))

    def _draw_clock(self, surface, session, t):
        width = self.size[0]
        box = pygame.Rect(width - 244, 22, 220, 88)
        panel(surface, box)
        urgent = session.time_left <= settings.TIME_WARNING
        pulse = 0.6 + 0.4 * math.sin(t * 8)
        color = settings.TEXT_COLOR
        if urgent:
            color = [int(c) for c in (255 * pulse, 90 * pulse, 80 * pulse)]
        surface.blit(
            self.fonts.label.render("TIME", True, settings.TEXT_DIM), (box.x + 18, box.y + 12)
        )
        time_image = self.fonts.heading.render(format_time(session.time_left), True, color)
        surface.blit(time_image, time_image.get_rect(topright=(box.right - 18, box.y + 6)))
        surface.blit(
            self.fonts.label.render("SCORE", True, settings.TEXT_DIM), (box.x + 18, box.y + 62)
        )
        score_image = self.fonts.body.render(str(session.score), True, settings.TEXT_COLOR)
        surface.blit(score_image, score_image.get_rect(topright=(box.right - 18, box.y + 56)))

    def _draw_objective(self, surface, session):
        width, height = self.size
        box = pygame.Rect(0, 0, 620, 62)
        box.center = (width / 2, height - 52)
        panel(surface, box)
        step = f"OBJECTIVE {session.objective_index + 1}/{len(OBJECTIVES)}"
        surface.blit(self.fonts.label.render(step, True, settings.ACCENT), (box.x + 18, box.y + 10))
        draw_centered(
            surface,
            self.fonts.body,
            session.objective,
            settings.TEXT_COLOR,
            (box.centerx, box.y + 40),
        )

    def _draw_prompt(self, surface, session):
        target = session.interaction_target()
        if target is None:
            return
        text = session.prompt_for(target)
        width, height = self.size
        label = self.fonts.body.render(text, True, settings.TEXT_COLOR)
        box = pygame.Rect(0, 0, label.get_width() + 92, 44)
        box.center = (width / 2, height - 134)
        panel(surface, box)
        cap = pygame.Rect(box.x + 12, box.y + 9, 26, 26)
        pygame.draw.rect(surface, settings.ACCENT, cap, border_radius=4)
        draw_centered(surface, self.fonts.label, "E", (14, 16, 20), cap.center)
        surface.blit(label, (cap.right + 14, box.y + 10))

    def _draw_toasts(self, surface):
        width = self.size[0]
        for i, (text, ttl) in enumerate(reversed(self.toasts)):
            image = self.fonts.body.render(text, True, settings.TEXT_COLOR)
            image.set_alpha(int(255 * min(1.0, ttl / 0.6)))
            surface.blit(image, image.get_rect(center=(width / 2, 140 + i * 30)))
