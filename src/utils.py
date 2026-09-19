"""Small math helpers shared across modules."""

import pygame


def clamp(value, low, high):
    return max(low, min(high, value))


def approach(value, target, step):
    """Move value toward target by at most step."""
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def distance_to_rect(point, rect):
    nearest = pygame.Vector2(
        clamp(point[0], rect.left, rect.right), clamp(point[1], rect.top, rect.bottom)
    )
    return nearest.distance_to(point)


def format_time(seconds):
    seconds = max(0, int(seconds + 0.999))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
