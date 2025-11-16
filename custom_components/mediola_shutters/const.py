"""Constants for the Mediola Shutters integration."""

DOMAIN = "mediola_shutters"

# Device type identifiers in Mediola
DEVICE_TYPE_WR = "WR"  # WIR shutters
DEVICE_TYPE_ER = "ER"  # Elero shutters

# Manufacturer names
MANUFACTURER_WIR = "WIR"
MANUFACTURER_ELERO = "Elero"
MANUFACTURER_UNKNOWN = "Unknown"

# Configuration keys
CONF_SCAN_INTERVAL = "scan_interval"

# Default scan interval in seconds
DEFAULT_SCAN_INTERVAL = 15

# Elero state codes
ELERO_STATE_OPEN = "1001"  # Fully open
ELERO_STATE_CLOSED = "1002"  # Fully closed
ELERO_STATE_INTERMEDIATE = "100D"  # Somewhere in between
ELERO_STATE_MOVING_UP = "100A"  # Moving upwards
ELERO_STATE_MOVING_DOWN = "100B"  # Moving downwards

# Elero commands
ELERO_CMD_UP = "08"  # Open/Up
ELERO_CMD_DOWN = "09"  # Close/Down
ELERO_CMD_STOP = "02"  # Stop