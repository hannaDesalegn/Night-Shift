"""Lightmap lighting.

Light is accumulated additively into an RGB lightmap which is then multiplied onto the
scene (BLEND_RGB_MULT). Unlit areas keep only the dim ambient color. Plain RGB
blits are much cheaper than per-pixel alpha overlays, and lights get color for free.
"""

import functools
import math

import pygame

from src import settings


def scale_color(color, k):
    return tuple(min(255, int(c * k)) for c in color)


@functools.lru_cache(maxsize=64)
def point_light(radius, color):
    """Radial gradient on black, meant to be added into the lightmap."""
    tex = pygame.Surface((radius * 2, radius * 2)).convert()
    tex.fill((0, 0, 0))
    steps = max(8, radius // 3)
    for i in range(steps):
        r = radius * (1 - i / steps)
        pygame.draw.circle(tex, scale_color(color, ((i + 1) / steps) ** 1.6), (radius, radius), r)
    return tex


def sample_rays(world, origin, radius, facing, half_angle, rays):
    """(angle, dx, dy, distance) per ray: how far light travels before hitting a wall."""
    samples = []
    for i in range(rays + 1):
        angle = facing - half_angle + 2 * half_angle * i / rays
        dist = world.cast_ray(origin, angle, radius)
        samples.append((angle, math.cos(angle), math.sin(angle), dist))
    return samples


def draw_light_layers(target, center, samples, radius, color, facing, half_angle, layers):
    """Paint wall-clipped light into target.

    Polygons are drawn from the outside in; each overwrites the previous one with a
    brighter color, which gives a stepped radial falloff without per-pixel work.
    """
    full_circle = half_angle >= math.pi
    cx, cy = center
    for layer in range(layers):
        t = 1 - layer / layers
        reach = radius * t
        # Inner layers narrow toward the beam's axis for a soft hotspot.
        arc = math.pi if full_circle else half_angle * (0.5 + 0.5 * t)
        points = [] if full_circle else [center]
        for angle, dx, dy, dist in samples:
            if full_circle or abs(angle - facing) <= arc:
                d = dist if dist < reach else reach
                points.append((cx + dx * d, cy + dy * d))
        if len(points) >= 3:
            shade = scale_color(color, ((layer + 1) / layers) ** 0.8)
            pygame.draw.polygon(target, shade, points)


class Lighting:
    def __init__(self, world, view_size=(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)):
        self.world = world
        self.lightmap = pygame.Surface(view_size).convert()
        size = settings.FLASHLIGHT_RANGE * 2
        self.beam_buffer = pygame.Surface((size, size)).convert()
        self._static = {}

    def static_map(self, powered):
        # Built lazily: the powered map is only needed once the generator runs.
        if powered not in self._static:
            self._static[powered] = self._build_static(powered)
        return self._static[powered]

    def _build_static(self, powered):
        surface = pygame.Surface(self.world.pixel_size).convert()
        surface.fill(settings.AMBIENT_POWERED if powered else settings.AMBIENT)
        layout = self.world.layout
        radius = settings.EMERGENCY_LIGHT_RADIUS
        tex = point_light(radius, settings.EMERGENCY_LIGHT_COLOR)
        for pos in layout.emergency_lights:
            surface.blit(tex, pos - (radius, radius), special_flags=pygame.BLEND_RGB_ADD)
        if powered:
            for pos in layout.lamps:
                self._add_lamp(surface, pos)
        return surface

    def _add_lamp(self, surface, pos):
        radius = settings.LAMP_RADIUS
        samples = sample_rays(self.world, pos, radius, 0.0, math.pi, 160)
        local = pygame.Surface((radius * 2, radius * 2)).convert()
        local.fill((0, 0, 0))
        center = (radius, radius)
        draw_light_layers(local, center, samples, radius, settings.LAMP_COLOR, 0, math.pi, 12)
        surface.blit(local, pos - (radius, radius), special_flags=pygame.BLEND_RGB_ADD)

    def render(self, surface, camera, powered, lights, beam=None):
        """Light the already-drawn scene on surface.

        lights: iterable of (world_pos, radius, color) point lights.
        beam: optional (world_pos, facing, radius, color) flashlight cone.
        """
        offset = camera.offset
        width, height = self.lightmap.get_size()
        self.lightmap.blit(self.static_map(powered), (0, 0), pygame.Rect(offset, (width, height)))
        for pos, radius, color in lights:
            x, y = pos[0] - offset.x - radius, pos[1] - offset.y - radius
            if -2 * radius < x < width and -2 * radius < y < height:
                tex = point_light(int(radius), color)
                self.lightmap.blit(tex, (x, y), special_flags=pygame.BLEND_RGB_ADD)
        if beam is not None:
            self._render_beam(offset, *beam)
        surface.blit(self.lightmap, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def _render_beam(self, offset, pos, facing, radius, color):
        half = settings.FLASHLIGHT_HALF_ANGLE
        samples = sample_rays(self.world, pos, radius, facing, half, settings.FLASHLIGHT_RAYS)
        buffer = self.beam_buffer
        buffer.fill((0, 0, 0))
        center = pygame.Vector2(buffer.get_size()) / 2
        draw_light_layers(buffer, center, samples, radius, color, facing, half, 10)
        self.lightmap.blit(buffer, pos - offset - center, special_flags=pygame.BLEND_RGB_ADD)
