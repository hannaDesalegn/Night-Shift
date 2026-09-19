"""Facility layout, tile collision, line of sight and grid pathing."""

import math
from collections import deque
from dataclasses import dataclass

import pygame

from src.settings import TILE

# Legend
#   #  wall                 T  desk            S  shelf          =  crates
#   M  machinery            O  pillar          G  generator      D  restricted door
#   X  exit gate            Z  loading dock    P  player start   K  keycard
#   C  generator component  B  battery         L  ceiling lamp   R  emergency light
#   1-9 enemy patrol route (in order)
FACILITY_MAP = (
    "############################################",
    "#..........#.............#.................#",
    "#.TT...TT..#.SSS.SSS.SSS.#.==...........==.#",
    "#.TT...TT..#.....4.......#........GG.......#",
    "#....L.....#.SSS.SSS.SSS.#........GG.......#",
    "#.TT...TT..#......L......#.................#",
    "#.TT...TT.K#.SSS.SSS.SSS.#...L....5....L...#",
    "#..........#...........B.#.==...........==.#",
    "#SS.......S#==.........==#.................#",
    "########..#######...#############...########",
    "#...R..............R...............R.......#",
    "#....1.....O.........O..........O......2...#",
    "#..........................................#",
    "#####...############DD##############...#####",
    "#............#...............#.............#",
    "#.==......==.#.MMM.MMMMM.MMM.#.==.......==.#",
    "#............#...............#.............#",
    "#....L.......#...............#......L......#",
    "#............#......L........#.....3.......#",
    "#.TTTT.......#.MM.......MM...#.............#",
    "#.TTTT.......#.MM..B....MM...#.==.......==.#",
    "#............#...............#.............#",
    "#............#MMMMMM...MMMMMM#.............#",
    "#..........R.#...............######XXX######",
    "#............#.==...6...==...#ZZZZZZZZZZZZZ#",
    "#............#......L........#ZZZZZZZZZZZZZ#",
    "#.....P......#...............#ZZZZZZZZZZZZZ#",
    "#............#.............C.#ZZZZZZZZZZZZZ#",
    "#............#==...........==#ZZZZZZZZZZZZZ#",
    "############################################",
)

SOLID_TILES = frozenset("#TS=MOG")
# Low furniture blocks movement but not light or sight.
OPAQUE_TILES = frozenset("#SMO")

ROOMS = {
    "OFFICE": (1, 1, 10, 8),
    "STORAGE": (12, 1, 13, 8),
    "GENERATOR ROOM": (26, 1, 17, 8),
    "CORRIDOR": (1, 10, 42, 3),
    "LOBBY": (1, 14, 12, 15),
    "MAINTENANCE": (14, 14, 15, 15),
    "EXIT BAY": (30, 14, 13, 9),
    "LOADING DOCK": (30, 24, 13, 5),
}

PICKUP_CODES = {"K": "keycard", "C": "component", "B": "battery"}


@dataclass
class Layout:
    player_start: pygame.Vector2
    pickups: list
    door_tiles: dict
    generator_tiles: list
    lamps: list
    emergency_lights: list
    patrol_points: list
    escape_tiles: set


def tile_center(col, row):
    return pygame.Vector2((col + 0.5) * TILE, (row + 0.5) * TILE)


class World:
    def __init__(self, rows=FACILITY_MAP):
        self.rows = rows
        self.cols = len(rows[0])
        self.height = len(rows)
        self.pixel_size = (self.cols * TILE, self.height * TILE)
        # Tiles temporarily blocked by closed doors.
        self.closed = set()
        self.layout = self._parse()

    def _parse(self):
        pickups, lamps, emergency, escape, generator = [], [], [], set(), []
        doors = {"D": [], "X": []}
        patrol = {}
        start = None
        for r, line in enumerate(self.rows):
            for c, ch in enumerate(line):
                center = tile_center(c, r)
                if ch == "P":
                    start = center
                elif ch in PICKUP_CODES:
                    pickups.append((PICKUP_CODES[ch], center))
                elif ch in doors:
                    doors[ch].append((c, r))
                elif ch == "G":
                    generator.append((c, r))
                elif ch == "L":
                    lamps.append(center)
                elif ch == "R":
                    emergency.append(center)
                elif ch == "Z":
                    escape.add((c, r))
                elif ch.isdigit():
                    patrol[int(ch)] = center
        return Layout(
            player_start=start,
            pickups=pickups,
            door_tiles=doors,
            generator_tiles=generator,
            lamps=lamps,
            emergency_lights=emergency,
            patrol_points=[patrol[k] for k in sorted(patrol)],
            escape_tiles=escape,
        )

    # --- tile queries -------------------------------------------------

    def char_at(self, col, row):
        if 0 <= row < self.height and 0 <= col < self.cols:
            return self.rows[row][col]
        return "#"

    def is_solid(self, col, row):
        return self.char_at(col, row) in SOLID_TILES or (col, row) in self.closed

    def is_opaque(self, col, row):
        return self.char_at(col, row) in OPAQUE_TILES or (col, row) in self.closed

    def tile_of(self, pos):
        return int(pos[0] // TILE), int(pos[1] // TILE)

    def room_at(self, pos):
        col, row = self.tile_of(pos)
        for name, (x, y, w, h) in ROOMS.items():
            if x <= col < x + w and y <= row < y + h:
                return name
        return None

    def is_escape(self, pos):
        return self.tile_of(pos) in self.layout.escape_tiles

    def set_closed(self, tiles, closed):
        if closed:
            self.closed.update(tiles)
        else:
            self.closed.difference_update(tiles)

    # --- collision ------------------------------------------------------

    def _overlapping_solids(self, x, y, w, h):
        # Shrink by a hair so a box resting flush against a wall does not count as overlapping.
        left, top = int(x // TILE), int(y // TILE)
        right, bottom = int((x + w - 1e-6) // TILE), int((y + h - 1e-6) // TILE)
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if self.is_solid(col, row):
                    yield col, row

    def move_box(self, x, y, w, h, dx, dy):
        """Move an axis-aligned box, resolving each axis separately so it slides along walls."""
        if dx:
            x += dx
            for col, _ in self._overlapping_solids(x, y, w, h):
                x = col * TILE - w if dx > 0 else (col + 1) * TILE
        if dy:
            y += dy
            for _, row in self._overlapping_solids(x, y, w, h):
                y = row * TILE - h if dy > 0 else (row + 1) * TILE
        return x, y

    def box_blocked(self, x, y, w, h):
        return next(self._overlapping_solids(x, y, w, h), None) is not None

    # --- sight ----------------------------------------------------------

    def cast_ray(self, origin, angle, max_dist):
        """Distance from origin to the first opaque tile along angle (DDA grid walk)."""
        ox, oy = origin[0] / TILE, origin[1] / TILE
        dx, dy = math.cos(angle), math.sin(angle)
        col, row = int(ox), int(oy)
        step_c = 1 if dx > 0 else -1
        step_r = 1 if dy > 0 else -1
        delta_c = abs(1 / dx) if dx else math.inf
        delta_r = abs(1 / dy) if dy else math.inf
        side_c = ((col + 1 - ox) if dx > 0 else (ox - col)) * delta_c
        side_r = ((row + 1 - oy) if dy > 0 else (oy - row)) * delta_r
        limit = max_dist / TILE
        while True:
            if side_c < side_r:
                dist, side_c, col = side_c, side_c + delta_c, col + step_c
            else:
                dist, side_r, row = side_r, side_r + delta_r, row + step_r
            if dist >= limit:
                return max_dist
            if self.is_opaque(col, row):
                return dist * TILE

    def line_of_sight(self, a, b):
        offset = pygame.Vector2(b) - pygame.Vector2(a)
        dist = offset.length()
        if dist < 1:
            return True
        angle = math.atan2(offset.y, offset.x)
        return self.cast_ray(a, angle, dist) >= dist

    # --- pathing --------------------------------------------------------

    def find_path(self, start, goal):
        """Breadth-first search over walkable tiles; returns waypoint centers or None."""
        start_t, goal_t = self.tile_of(start), self.tile_of(goal)
        if self.is_solid(*goal_t):
            return None
        came_from = {start_t: None}
        queue = deque([start_t])
        while queue:
            current = queue.popleft()
            if current == goal_t:
                break
            for nxt in self._neighbours(current):
                if nxt not in came_from:
                    came_from[nxt] = current
                    queue.append(nxt)
        if goal_t not in came_from:
            return None
        path = []
        node = goal_t
        while node != start_t:
            path.append(tile_center(*node))
            node = came_from[node]
        path.reverse()
        return path

    def _neighbours(self, tile):
        col, row = tile
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nc, nr = col + dc, row + dr
            if self.is_solid(nc, nr):
                continue
            # Disallow diagonal steps that would clip a wall corner.
            if dc and dr and (self.is_solid(col + dc, row) or self.is_solid(col, row + dr)):
                continue
            yield nc, nr
