"""World-space drawing: the pre-rendered facility and the camera that frames it."""

import functools
import math
import random

import pygame

from src import settings
from src.settings import TILE
from src.world import ROOMS

FLOOR_TINTS = {
    "OFFICE": (34, 31, 40),
    "STORAGE": (31, 31, 30),
    "GENERATOR ROOM": (29, 31, 34),
    "CORRIDOR": (30, 32, 37),
    "LOBBY": (32, 33, 38),
    "MAINTENANCE": (27, 31, 33),
    "EXIT BAY": (30, 31, 34),
    "LOADING DOCK": (22, 22, 24),
}
DEFAULT_FLOOR = (28, 30, 35)
WALL_TOP = (52, 56, 68)
WALL_EDGE = (78, 84, 100)
WALL_FACE = (34, 37, 46)
WALL_FACE_HEIGHT = 12
SHADOW = (0, 0, 0, 90)


def _shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


class Camera:
    def __init__(self, world_size, view_size=(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)):
        self.world_w, self.world_h = world_size
        self.view_w, self.view_h = view_size
        self.pos = pygame.Vector2()

    def _clamped(self, target):
        x = min(max(target.x - self.view_w / 2, 0), self.world_w - self.view_w)
        y = min(max(target.y - self.view_h / 2, 0), self.world_h - self.view_h)
        return pygame.Vector2(x, y)

    def snap(self, target):
        self.pos = self._clamped(pygame.Vector2(target))

    def follow(self, target, dt):
        goal = self._clamped(pygame.Vector2(target))
        # Frame-rate independent exponential smoothing.
        self.pos += (goal - self.pos) * min(1.0, settings.CAMERA_SMOOTHING * dt)

    @property
    def offset(self):
        return pygame.Vector2(round(self.pos.x), round(self.pos.y))

    def to_screen(self, world_pos):
        return pygame.Vector2(world_pos) - self.offset


def build_world_surface(world, fonts):
    """Draw every static tile once; the result is blitted through the camera each frame."""
    surface = pygame.Surface(world.pixel_size).convert()
    rng = random.Random(1987)
    _draw_floors(surface, world, rng)
    _draw_room_labels(surface, fonts)
    _draw_shadows(surface, world)
    for row in range(world.height):
        for col in range(world.cols):
            ch = world.char_at(col, row)
            rect = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
            painter = _TILE_PAINTERS.get(ch)
            if painter:
                painter(surface, rect, world, col, row, rng)
    return surface


def _floor_color(world, col, row):
    room = world.room_at(((col + 0.5) * TILE, (row + 0.5) * TILE))
    return FLOOR_TINTS.get(room, DEFAULT_FLOOR), room


def _draw_floors(surface, world, rng):
    for row in range(world.height):
        for col in range(world.cols):
            rect = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
            base, room = _floor_color(world, col, row)
            if room == "LOBBY" and (col + row) % 2:
                base = _shade(base, 4)
            surface.fill(base, rect)
            if room == "LOADING DOCK":
                _paint_asphalt(surface, rect, rng)
                continue
            pygame.draw.rect(surface, _shade(base, -7), rect, 1)
            if room == "MAINTENANCE":
                grate = _shade(base, -5)
                for x in range(rect.x + 8, rect.right, 8):
                    pygame.draw.line(surface, grate, (x, rect.y + 2), (x, rect.bottom - 3))
            for _ in range(3):
                spot = (rect.x + rng.randrange(TILE), rect.y + rng.randrange(TILE))
                surface.set_at(spot, _shade(base, rng.choice((-6, 6))))


def _paint_asphalt(surface, rect, rng):
    for _ in range(10):
        spot = (rect.x + rng.randrange(TILE), rect.y + rng.randrange(TILE))
        surface.set_at(spot, _shade((22, 22, 24), rng.randrange(-5, 9)))


def _draw_room_labels(surface, fonts):
    for name, (x, y, w, h) in ROOMS.items():
        label = fonts.stencil.render(name, True, (255, 255, 255))
        label.set_alpha(16)
        area = pygame.Rect(x * TILE, y * TILE, w * TILE, h * TILE)
        pos = label.get_rect(midbottom=(area.centerx, area.bottom - 10))
        surface.blit(label, pos)


def _draw_shadows(surface, world):
    shadow = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    shadow.fill(SHADOW)
    for row in range(world.height):
        for col in range(world.cols):
            if world.is_solid(col, row) and world.char_at(col, row) != "#":
                surface.blit(shadow, (col * TILE + 5, row * TILE + 7))


def _merged_rect(rect, world, col, row, inset_x, inset_y):
    """Inset a tile only on sides that do not continue the same furniture piece."""
    ch = world.char_at(col, row)
    left = 0 if world.char_at(col - 1, row) == ch else inset_x
    right = 0 if world.char_at(col + 1, row) == ch else inset_x
    top = 0 if world.char_at(col, row - 1) == ch else inset_y
    bottom = 0 if world.char_at(col, row + 1) == ch else inset_y
    return pygame.Rect(rect.x + left, rect.y + top, TILE - left - right, TILE - top - bottom)


def _paint_wall(surface, rect, world, col, row, rng):
    surface.fill(WALL_TOP, rect)
    # Highlight edges that face open floor so rooms read clearly from above.
    if world.char_at(col, row - 1) != "#":
        pygame.draw.line(surface, WALL_EDGE, rect.topleft, rect.topright, 2)
    if world.char_at(col - 1, row) != "#":
        pygame.draw.line(surface, WALL_EDGE, rect.topleft, rect.bottomleft, 2)
    if world.char_at(col + 1, row) != "#":
        pygame.draw.line(surface, _shade(WALL_TOP, -12), rect.topright, rect.bottomright, 2)
    if world.char_at(col, row + 1) != "#":
        face = pygame.Rect(rect.x, rect.bottom - WALL_FACE_HEIGHT, TILE, WALL_FACE_HEIGHT)
        surface.fill(WALL_FACE, face)
        pygame.draw.line(surface, _shade(WALL_FACE, -10), face.bottomleft, face.bottomright, 2)
    if rng.random() < 0.15:
        crack = (rect.x + rng.randrange(8, 40), rect.y + rng.randrange(8, 30))
        pygame.draw.line(surface, _shade(WALL_TOP, -10), crack, (crack[0] + 6, crack[1] + 4))


def _paint_desk(surface, rect, world, col, row, rng):
    top = _merged_rect(rect, world, col, row, 3, 5)
    surface.fill((78, 60, 46), top)
    surface.fill((96, 76, 56), _merged_rect(rect, world, col, row, 6, 8))
    if (col + row) % 2 == 0:
        monitor = pygame.Rect(0, 0, 18, 12)
        monitor.center = top.center
        pygame.draw.rect(surface, (20, 24, 30), monitor, border_radius=2)
        pygame.draw.rect(surface, (40, 70, 80), monitor.inflate(-4, -4))
    else:
        paper = pygame.Rect(top.x + 8, top.y + 6, 12, 15)
        pygame.draw.rect(surface, (170, 170, 160), paper)


def _paint_shelf(surface, rect, world, col, row, rng):
    frame = _merged_rect(rect, world, col, row, 3, 6)
    surface.fill((58, 62, 70), frame)
    pygame.draw.line(surface, (40, 43, 50), frame.topleft, frame.topright, 2)
    pygame.draw.line(surface, (40, 43, 50), frame.bottomleft, frame.bottomright, 2)
    x = frame.x + 4
    while x < frame.right - 8:
        w = rng.randrange(7, 13)
        color = rng.choice(((110, 86, 56), (92, 74, 50), (70, 84, 96), (120, 110, 90)))
        pygame.draw.rect(surface, color, (x, frame.y + 5, w, frame.height - 10))
        x += w + 2


def _paint_crates(surface, rect, world, col, row, rng):
    box = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (96, 74, 46), box, border_radius=2)
    pygame.draw.rect(surface, (64, 48, 30), box, 3, border_radius=2)
    pygame.draw.line(surface, (70, 52, 32), box.topleft, box.bottomright, 3)
    pygame.draw.line(surface, (70, 52, 32), box.topright, box.bottomleft, 3)


def _paint_machine(surface, rect, world, col, row, rng):
    body = _merged_rect(rect, world, col, row, 3, 3)
    surface.fill((40, 58, 60), body)
    pygame.draw.rect(surface, (58, 80, 82), rect.inflate(-10, -10), 2, border_radius=2)
    for corner in (body.topleft, body.topright, body.bottomleft, body.bottomright):
        rivet = pygame.Vector2(corner) + (pygame.Vector2(body.center) - corner) * 0.2
        pygame.draw.circle(surface, (90, 110, 110), rivet, 2)
    if rng.random() < 0.4:
        pygame.draw.circle(surface, (30, 44, 46), body.center, 8)
        pygame.draw.circle(surface, (80, 100, 100), body.center, 8, 2)


def _paint_pillar(surface, rect, world, col, row, rng):
    pygame.draw.rect(surface, (60, 64, 74), rect.inflate(-6, -6), border_radius=4)
    pygame.draw.rect(surface, (80, 86, 98), rect.inflate(-14, -14), border_radius=3)


def _paint_dock(surface, rect, world, col, row, rng):
    if col % 4 == 0:
        pygame.draw.line(surface, (120, 104, 40), rect.midtop, rect.midbottom, 3)


_TILE_PAINTERS = {
    "#": _paint_wall,
    "T": _paint_desk,
    "S": _paint_shelf,
    "=": _paint_crates,
    "M": _paint_machine,
    "O": _paint_pillar,
    "Z": _paint_dock,
}


def _polar(origin, angle, dist):
    return pygame.Vector2(origin) + pygame.Vector2(math.cos(angle), math.sin(angle)) * dist


def draw_player(surface, player, camera):
    # Flicker while invulnerable so the grace window is readable.
    if player.invulnerable > 0 and int(player.invulnerable * 14) % 2:
        return
    center = camera.to_screen(player.pos)
    angle = player.facing
    side = angle + math.pi / 2
    swing = math.sin(player.stride * 0.09) * 5 if player.moving else 0

    surface.blit(_contact_shadow(32, 30), center - (13, 11))
    # Hands swing opposite each other while walking; the right hand holds the torch.
    left_hand = _polar(_polar(center, side, -12), angle, 3 - swing)
    right_hand = _polar(_polar(center, side, 11), angle, 8 + swing * 0.3)
    pygame.draw.circle(surface, (196, 160, 130), left_hand, 4)
    pygame.draw.circle(surface, (196, 160, 130), right_hand, 4)
    torch_tip = _polar(right_hand, angle, 9)
    pygame.draw.line(surface, (70, 74, 82), right_hand, torch_tip, 5)

    pygame.draw.circle(surface, (38, 62, 96), center, 13)
    pygame.draw.circle(surface, (22, 36, 58), center, 13, 2)
    # Reflective shoulder strip across the jacket.
    strip = (_polar(center, side, -10), _polar(center, side, 10))
    pygame.draw.line(surface, (210, 190, 70), *strip, 3)
    brim = [_polar(center, a, r) for a, r in ((angle, 12), (angle + 0.9, 7), (angle - 0.9, 7))]
    pygame.draw.polygon(surface, (20, 24, 32), brim)
    pygame.draw.circle(surface, (64, 74, 96), center, 8)
    pygame.draw.circle(surface, (20, 24, 32), center, 8, 2)
    pygame.draw.circle(surface, (210, 190, 70), _polar(center, angle, 3), 2)


PICKUP_COLORS = {
    "keycard": (236, 168, 60),
    "component": (80, 220, 230),
    "battery": (120, 220, 110),
}


@functools.lru_cache(maxsize=64)
def glow_texture(color, radius, strength):
    """Radial glow with color premultiplied into RGB, meant for additive blits."""
    tex = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -2):
        k = strength * (1 - r / radius) ** 2
        pygame.draw.circle(tex, [int(c * k) for c in color], (radius, radius), r)
    return tex


def draw_glow(surface, center, color, radius, strength=1.0):
    # Quantize strength so pulsing glows reuse a handful of cached textures.
    tex = glow_texture(color, radius, round(strength, 1))
    surface.blit(tex, (center[0] - radius, center[1] - radius), special_flags=pygame.BLEND_RGB_ADD)


@functools.lru_cache(maxsize=8)
def _contact_shadow(width, height):
    shadow = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
    return shadow


def draw_pickup(surface, pickup, camera, t):
    color = PICKUP_COLORS[pickup.kind]
    bob = math.sin(t * 3 + pickup.pos.x) * 3
    center = camera.to_screen(pickup.pos) + (0, bob)
    pulse = 0.75 + 0.25 * math.sin(t * 4 + pickup.pos.y)
    draw_glow(surface, center, color, 34, 0.45 * pulse)
    surface.blit(_contact_shadow(22, 8), (center.x - 11, center.y + 12 - bob))
    if pickup.kind == "keycard":
        card = pygame.Rect(0, 0, 22, 15)
        card.center = center
        pygame.draw.rect(surface, color, card, border_radius=3)
        pygame.draw.rect(surface, (60, 40, 20), card.inflate(-2, -8).move(0, -2))
        pygame.draw.rect(surface, (255, 240, 200), (card.x + 3, card.bottom - 5, 7, 2))
    elif pickup.kind == "component":
        body = pygame.Rect(0, 0, 12, 22)
        body.center = center
        pygame.draw.rect(surface, (40, 60, 70), body.inflate(4, 0), border_radius=3)
        pygame.draw.rect(surface, color, body.inflate(-2, -8), border_radius=2)
        for y in (body.top, body.bottom - 4):
            pygame.draw.rect(surface, (180, 190, 200), (body.x - 1, y, 14, 4), border_radius=1)
    else:
        body = pygame.Rect(0, 0, 18, 11)
        body.center = center
        pygame.draw.rect(surface, (30, 40, 30), body, border_radius=2)
        fill = body.inflate(-4, -4)
        pygame.draw.rect(surface, color, fill, border_radius=1)
        pygame.draw.rect(surface, (200, 200, 200), (body.right, body.centery - 2, 3, 4))


DOOR_STEEL = (74, 80, 92)
DOOR_TRIM = (150, 120, 40)
LIGHT_LOCKED = (230, 60, 50)
LIGHT_READY = (240, 180, 60)
LIGHT_OPEN = (90, 220, 120)


def draw_door(surface, door, camera, t):
    rect = door.rect.move(-camera.offset)
    surface.fill((18, 19, 24), rect)
    shake = math.sin(t * 70) * 3 * (door.rattle / 0.35) if door.rattle else 0
    # Each half slides into the wall on its own side.
    half_w = rect.width / 2
    slide = half_w * _ease_in_out(door.open_amount)
    frame = rect.inflate(0, -14)
    for sign in (-1, 1):
        panel_w = half_w - slide
        if panel_w <= 1:
            continue
        x = rect.x + shake if sign < 0 else rect.centerx + slide + shake
        panel = pygame.Rect(round(x), frame.y, round(panel_w), frame.height)
        surface.fill(DOOR_STEEL, panel)
        pygame.draw.rect(surface, (48, 52, 62), panel, 2)
        stripe = pygame.Rect(panel.x, panel.bottom - 7, panel.width, 5)
        surface.fill(DOOR_TRIM, stripe)


def draw_door_lamp(surface, door, camera, t, can_open, highlighted):
    if door.is_open:
        color = LIGHT_OPEN
    elif can_open:
        color = LIGHT_READY
    else:
        color = LIGHT_LOCKED
    # The lamp pulses faster when the player is close enough to use the door.
    speed = 8 if highlighted else 2.5
    pulse = 0.6 + 0.4 * math.sin(t * speed)
    lamp = door_lamp_pos(door) - camera.offset
    pygame.draw.circle(surface, color, lamp, 3)
    draw_glow(surface, lamp, color, 26, (0.9 if highlighted else 0.5) * pulse)


def door_lamp_pos(door):
    return pygame.Vector2(door.rect.centerx, door.rect.y + 4)


def draw_emergency_light(surface, pos, camera, t):
    pulse = 0.5 + 0.5 * math.sin(t * 1.8 + pos[0] * 0.01)
    center = camera.to_screen(pos)
    draw_glow(surface, center, (200, 30, 24), 120, 0.25 + 0.2 * pulse)
    pygame.draw.circle(surface, (255, 80, 60), center, 3)


def _ease_in_out(x):
    return x * x * (3 - 2 * x)


def draw_generator(surface, generator, camera, t):
    state = generator.state
    starting = state == generator.STARTING
    online = state == generator.ONLINE
    shake = pygame.Vector2(math.sin(t * 53), math.cos(t * 41)) * 2 if starting else (0, 0)
    rect = generator.rect.move(-camera.offset).move(shake).inflate(-6, -6)

    surface.blit(_contact_shadow(rect.width + 10, 30), (rect.x - 2, rect.bottom - 16))
    pygame.draw.rect(surface, (46, 52, 60), rect, border_radius=6)
    pygame.draw.rect(surface, (26, 30, 36), rect, 3, border_radius=6)
    for y in range(rect.y + 10, rect.y + 26, 5):
        pygame.draw.line(surface, (30, 34, 40), (rect.right - 38, y), (rect.right - 10, y), 2)

    # Exhaust fan spins up with the start sequence.
    fan_center = (rect.x + 30, rect.centery + 6)
    pygame.draw.circle(surface, (20, 22, 26), fan_center, 22)
    spin = t * (14 if online else 14 * generator.progress**2)
    for i in range(4):
        tip = _polar(fan_center, spin + i * math.pi / 2, 18)
        pygame.draw.line(surface, (90, 98, 110), fan_center, tip, 5)
    pygame.draw.circle(surface, (120, 128, 140), fan_center, 5)

    slot = pygame.Rect(rect.right - 32, rect.y + 34, 14, 26)
    pygame.draw.rect(surface, (14, 16, 20), slot, border_radius=3)
    if state != generator.OFFLINE:
        pygame.draw.rect(surface, PICKUP_COLORS["component"], slot.inflate(-6, -6), border_radius=2)

    bar = pygame.Rect(rect.right - 40, rect.bottom - 16, 30, 6)
    pygame.draw.rect(surface, (14, 16, 20), bar)
    if online:
        indicator = LIGHT_OPEN
        pygame.draw.rect(surface, indicator, bar)
        draw_glow(surface, rect.center, (60, 200, 220), 90, 0.35 + 0.05 * math.sin(t * 6))
    elif starting:
        indicator = LIGHT_READY if int(t * 6) % 2 else (90, 70, 30)
        pygame.draw.rect(surface, LIGHT_READY, (bar.x, bar.y, bar.width * generator.progress, 6))
    else:
        indicator = LIGHT_LOCKED if int(t * 1.5) % 2 else (80, 30, 30)
    lamp = (rect.right - 14, rect.y + 12)
    pygame.draw.circle(surface, indicator, lamp, 4)
    draw_glow(surface, lamp, indicator, 22, 0.6)


ENEMY_BODY = (16, 12, 22)
ENEMY_RIM = (74, 42, 96)
ENEMY_EYES = {"patrol": (255, 190, 90), "search": (255, 140, 60), "chase": (255, 50, 50)}


def draw_enemy(surface, enemy, camera, t):
    center = camera.to_screen(enemy.pos)
    surface.blit(_contact_shadow(40, 30), center - (18, 9))
    breathe = math.sin(t * 3.1) * 1.5
    # Trailing wisps orbit the body to keep the silhouette unsettled.
    for i in range(5):
        a = t * 1.7 + i * math.tau / 5
        wisp = _polar(center, a, 14 + math.sin(t * 4 + i) * 3)
        pygame.draw.circle(surface, ENEMY_RIM, wisp, 5)
    pygame.draw.circle(surface, ENEMY_RIM, center, 17 + breathe)
    pygame.draw.circle(surface, ENEMY_BODY, center, 15 + breathe)
    head = _polar(center, enemy.facing, 5)
    pygame.draw.circle(surface, (8, 6, 12), head, 10)


def draw_enemy_eyes(surface, enemy, camera):
    """Drawn after the darkness pass so the eyes stay visible in unlit areas."""
    center = camera.to_screen(enemy.pos)
    color = ENEMY_EYES[enemy.state.value]
    head = _polar(center, enemy.facing, 9)
    for side in (-1, 1):
        eye = _polar(head, enemy.facing + side * math.pi / 2, 4)
        pygame.draw.circle(surface, color, eye, 2)
    draw_glow(surface, head, color, 26, 0.55)
