"""Centralized tuning values for Night Shift."""

TITLE = "Night Shift"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Clamp long frames (window drags, breakpoints) so physics never takes a huge step.
MAX_FRAME_TIME = 1 / 20

# Palette
BG_COLOR = (8, 9, 14)
TEXT_COLOR = (214, 218, 226)
TEXT_DIM = (120, 126, 140)
ACCENT = (242, 178, 72)
DANGER = (222, 64, 64)

# World
TILE = 48
CAMERA_SMOOTHING = 8.0

# Fonts: first installed match wins, otherwise pygame's bundled font.
FONT_NAMES = "consolas,dejavusansmono,menlo,couriernew"

# Player
PLAYER_SIZE = 26
PLAYER_SPEED = 205
# How quickly velocity reaches its target; higher feels snappier.
PLAYER_ACCEL = 16.0
PLAYER_TURN_RATE = 12.0
PLAYER_MAX_HEALTH = 100
PLAYER_INVULNERABLE_TIME = 1.5
PLAYER_KNOCKBACK = 420

# Interaction
PICKUP_RADIUS = 30
INTERACT_RADIUS = 64
BATTERY_CHARGE = 45
DOOR_OPEN_TIME = 0.7
DOOR_RATTLE_TIME = 0.35
GENERATOR_START_TIME = 3.0

# Enemy
ENEMY_SIZE = 30
# Index into the patrol route; the generator room keeps it away from the lobby start.
ENEMY_START_POST = 4
ENEMY_PATROL_SPEED = 85
ENEMY_TURN_RATE = 6.0
ENEMY_PATROL_PAUSE = 1.2
ENEMY_WAYPOINT_REACHED = 6
ENEMY_CHASE_SPEED = 172
ENEMY_SIGHT_RANGE = 300
# A lit flashlight gives the player away from much further.
ENEMY_LIT_SIGHT_RANGE = 460
ENEMY_CHASE_SIGHT_RANGE = 520
ENEMY_HEARING_RADIUS = 90
ENEMY_FOV = 1.9
# Time the player must stay in view before the enemy commits to a chase.
ENEMY_NOTICE_TIME = 0.35
ENEMY_LOSE_TIME = 0.7
ENEMY_REPATH_INTERVAL = 0.3
ENEMY_SEARCH_SPEED = 115
ENEMY_SEARCH_TIME = 6.0
ENEMY_SEARCH_RADIUS = 3
ENEMY_SEARCH_PAUSE = 0.6
ENEMY_DAMAGE = 25
ENEMY_CATCH_MARGIN = 3
# The enemy stalls after a hit so the player has a window to escape.
ENEMY_RECOVER_TIME = 1.3
