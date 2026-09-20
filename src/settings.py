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

# Run
TIME_LIMIT = 360.0
TIME_WARNING = 60.0

# World
TILE = 48
CAMERA_SMOOTHING = 8.0

# Fonts: first installed match wins, otherwise pygame's bundled font.
FONT_NAMES = "consolas,dejavusansmono,menlo,couriernew"

# Player
PLAYER_SIZE = 26
PLAYER_SPEED = 175
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
ENEMY_PATROL_SPEED = 78
ENEMY_TURN_RATE = 6.0
ENEMY_PATROL_PAUSE = 1.2
ENEMY_WAYPOINT_REACHED = 6
# Slightly slower than the player so a clean escape is always possible.
ENEMY_CHASE_SPEED = 152
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
ENEMY_SEARCH_SPEED = 100
ENEMY_SEARCH_TIME = 6.0
ENEMY_SEARCH_RADIUS = 3
ENEMY_SEARCH_PAUSE = 0.6
ENEMY_DAMAGE = 25
ENEMY_CATCH_MARGIN = 3
# The enemy stalls after a hit so the player has a window to escape.
ENEMY_RECOVER_TIME = 1.3

# Lighting: colors are added into a lightmap that multiplies the scene.
AMBIENT = (20, 20, 30)
AMBIENT_POWERED = (38, 38, 46)
EMERGENCY_LIGHT_RADIUS = 150
EMERGENCY_LIGHT_COLOR = (96, 20, 16)
LAMP_RADIUS = 300
LAMP_COLOR = (190, 180, 150)
PLAYER_GLOW_RADIUS = 90
PLAYER_GLOW_COLOR = (62, 62, 74)

# Flashlight
FLASHLIGHT_RANGE = 390
FLASHLIGHT_HALF_ANGLE = 0.5
FLASHLIGHT_RAYS = 48
FLASHLIGHT_COLOR = (255, 238, 205)
FLASHLIGHT_MAX_ENERGY = 100.0
# Roughly 90 seconds of continuous light from a full charge.
FLASHLIGHT_DRAIN = 1.1
# Slow trickle while switched off, so darkness is a choice rather than a dead end.
FLASHLIGHT_RECHARGE = 0.6
# After running dry it must recover this much before it will switch on again.
FLASHLIGHT_RESTART_ENERGY = 15.0
FLASHLIGHT_LOW = 25.0
# Weakest beam, as a fraction of full range, just before the battery dies.
FLASHLIGHT_MIN_REACH = 0.55

# Scoring
SCORE_PICKUP = {"keycard": 250, "component": 250, "battery": 50}
SCORE_POWER = 500
SCORE_ESCAPE = 1000
SCORE_PER_SECOND_LEFT = 5
SCORE_DAMAGE_PENALTY = 150

# Effects
MAX_PARTICLES = 260
SHAKE_MAX = 18
SHAKE_DECAY = 1.9
