
GENERIC_ERROR = -1  # Generic Error
GENERIC_OK = 0      # Generic success
GENERIC_CANCEL = 0

NEGATIVE_FILM = 0
POSITIVE_FILM = 1

IMAGE_ROTATED_270 = 1
IMAGE_ROTATED_90 = 2
IMAGE_ROTATED_180 = 3

# Colour array for quality indices (0-4)
QUALITY_COLOURS_16BIT_WORST_CASE = 4
QUALITY_COLOURS_16BIT_NON_RELATABLE = 5
QUALITY_COLOURS_16BIT_OUT_OF_SCALE = 6
QUALITY_COLOURS_16BIT = [
    0x22C55E,  # 0 - Green (excellent)
    0x84CC16,  # 1 - Lime (good)
    0xEAB308,  # 2 - Yellow (fair)
    0xF97326,  # 3 - Orange (poor)
    # 0xF97316,  # 3 - Orange (poor)
    #0xFFFFF9,  # 3 - Orange (poor)
    0xEF4444,  # 4 - Red (very poor)
    0xFF0000,  # 5 - Bright Red
    0x000000   # 7 - Black (out if range or not scaled)
]