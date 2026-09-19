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

# Interaction
PICKUP_RADIUS = 30
INTERACT_RADIUS = 64
BATTERY_CHARGE = 45
