import pygame

from src.utils import approach, distance_to_rect, format_time


def test_format_time_rounds_up_partial_seconds():
    assert format_time(272) == "04:32"
    assert format_time(0.2) == "00:01"
    assert format_time(-3) == "00:00"


def test_approach_never_overshoots():
    assert approach(0.0, 1.0, 0.4) == 0.4
    assert approach(0.9, 1.0, 0.4) == 1.0
    assert approach(1.0, 0.0, 0.25) == 0.75


def test_distance_to_rect_is_zero_inside():
    rect = pygame.Rect(0, 0, 10, 10)
    assert distance_to_rect((5, 5), rect) == 0
    assert distance_to_rect((13, 14), rect) == 5
