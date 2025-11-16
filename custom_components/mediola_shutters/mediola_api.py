"""API client for Mediola Gateway."""
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from .const import (
    DEVICE_TYPE_WR,
    DEVICE_TYPE_ER,
    MANUFACTURER_WIR,
    MANUFACTURER_ELERO,
    MANUFACTURER_UNKNOWN,
    ELERO_STATE_OPEN,
    ELERO_STATE_CLOSED,
    ELERO_STATE_INTERMEDIATE,
    ELERO_STATE_MOVING_UP,
    ELERO_STATE_MOVING_DOWN,
    ELERO_CMD_UP,
    ELERO_CMD_DOWN,
    ELERO_CMD_STOP,
)

_LOGGER = logging.getLogger(__name__)


class MediolaAPI:
    """Class to interact with Mediola Gateway."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize the API client."""
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"http://{host}/command"

    def _build_url(self, params: Dict[str, str]) -> str:
        """Build the full URL with authentication and parameters."""
        auth_params = {
            "XC_USER": self.username,
            "XC_PASS": self.password,
        }
        all_params = {**auth_params, **params}
        param_str = "&".join([f"{k}={v}" for k, v in all_params.items()])
        return f"{self.base_url}?{param_str}"

    def get_states(self) -> List[Dict[str, Any]]:
        """Get current states of all devices from the gateway."""
        url = self._build_url({"XC_FNC": "GetStates"})
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse response: remove {XC_SUC} prefix and parse JSON
            text = response.text
            if text.startswith("{XC_SUC}"):
                text = text[8:]  # Remove {XC_SUC} prefix
            
            devices = json.loads(text)
            
            # Filter only shutter devices (type "WR" or "ER")
            shutters = [
                d for d in devices 
                if d.get("type") in [DEVICE_TYPE_WR, DEVICE_TYPE_ER]
            ]
            
            return shutters
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error fetching states from Mediola gateway: %s", err)
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error("Error parsing response from Mediola gateway: %s", err)
            raise

    def get_manufacturer(self, device_type: str) -> str:
        """Get manufacturer name from device type.
        
        Args:
            device_type: Device type from gateway (e.g., "WR", "ER")
            
        Returns:
            Manufacturer name
        """
        if device_type == DEVICE_TYPE_WR:
            return MANUFACTURER_WIR
        elif device_type == DEVICE_TYPE_ER:
            return MANUFACTURER_ELERO
        else:
            return MANUFACTURER_UNKNOWN

    def send_command(self, device_type: str, adr: str, command: str) -> bool:
        """Send a command to a specific shutter.
        
        Args:
            device_type: Type of device ("WR" or "ER")
            adr: Address of the shutter
            command: Command string to send
            
        Returns:
            True if command was successful
        """
        params = {
            "XC_FNC": "SendSC",
            "type": device_type,
            "data": command
        }
        
        url = self._build_url(params)
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if response indicates success
            return "{XC_SUC}" in response.text
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error sending command to Mediola gateway: %s", err)
            return False

    # WIR (Type WR) specific methods
    def open_wir_shutter(self, sid: str, adr: str) -> bool:
        """Open a WIR shutter completely.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter (e.g., "2E105601")
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010101
        command = f"01{adr}010101"
        return self.send_command(DEVICE_TYPE_WR, adr, command)

    def close_wir_shutter(self, sid: str, adr: str) -> bool:
        """Close a WIR shutter completely.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010102
        command = f"01{adr}010102"
        return self.send_command(DEVICE_TYPE_WR, adr, command)

    def stop_wir_shutter(self, sid: str, adr: str) -> bool:
        """Stop a WIR shutter.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010103
        command = f"01{adr}010103"
        return self.send_command(DEVICE_TYPE_WR, adr, command)

    def set_wir_shutter_position(self, sid: str, adr: str, position: int) -> bool:
        """Set WIR shutter to a specific position.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            position: Position in percent (0 = open, 100 = closed)
            
        Returns:
            True if command was successful
        """
        # Convert position to hex (0-100 -> 00-64 in hex)
        position_hex = format(position, '02X')
        
        # Command format: 01 + adr + 0107 + position_hex
        command = f"01{adr}0107{position_hex}"
        return self.send_command(DEVICE_TYPE_WR, adr, command)

    # Elero (Type ER) specific methods
    def open_elero_shutter(self, sid: str, adr: str) -> bool:
        """Open an Elero shutter completely.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter (e.g., "09")
            
        Returns:
            True if command was successful
        
        Example:
            For shutter with adr "09": data=0908
        """
        # Command format: adr + 08 (UP command)
        command = f"{adr}{ELERO_CMD_UP}"
        return self.send_command(DEVICE_TYPE_ER, adr, command)

    def close_elero_shutter(self, sid: str, adr: str) -> bool:
        """Close an Elero shutter completely.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        
        Example:
            For shutter with adr "09": data=0909
        """
        # Command format: adr + 09 (DOWN command)
        command = f"{adr}{ELERO_CMD_DOWN}"
        return self.send_command(DEVICE_TYPE_ER, adr, command)

    def stop_elero_shutter(self, sid: str, adr: str) -> bool:
        """Stop an Elero shutter.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        
        Example:
            For shutter with adr "09": data=0902
        """
        # Command format: adr + 02 (STOP command)
        command = f"{adr}{ELERO_CMD_STOP}"
        return self.send_command(DEVICE_TYPE_ER, adr, command)

    # Unified interface methods
    def open_shutter(self, device_type: str, sid: str, adr: str) -> bool:
        """Open a shutter (works for both WIR and Elero).
        
        Args:
            device_type: Type of device ("WR" or "ER")
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        if device_type == DEVICE_TYPE_WR:
            return self.open_wir_shutter(sid, adr)
        elif device_type == DEVICE_TYPE_ER:
            return self.open_elero_shutter(sid, adr)
        else:
            _LOGGER.error("Unknown device type: %s", device_type)
            return False

    def close_shutter(self, device_type: str, sid: str, adr: str) -> bool:
        """Close a shutter (works for both WIR and Elero).
        
        Args:
            device_type: Type of device ("WR" or "ER")
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        if device_type == DEVICE_TYPE_WR:
            return self.close_wir_shutter(sid, adr)
        elif device_type == DEVICE_TYPE_ER:
            return self.close_elero_shutter(sid, adr)
        else:
            _LOGGER.error("Unknown device type: %s", device_type)
            return False

    def stop_shutter(self, device_type: str, sid: str, adr: str) -> bool:
        """Stop a shutter (works for both WIR and Elero).
        
        Args:
            device_type: Type of device ("WR" or "ER")
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        if device_type == DEVICE_TYPE_WR:
            return self.stop_wir_shutter(sid, adr)
        elif device_type == DEVICE_TYPE_ER:
            return self.stop_elero_shutter(sid, adr)
        else:
            _LOGGER.error("Unknown device type: %s", device_type)
            return False

    def set_shutter_position(self, device_type: str, sid: str, adr: str, position: int) -> bool:
        """Set shutter to a specific position.
        
        Note: Only supported for WIR shutters. Elero shutters don't support positioning.
        
        Args:
            device_type: Type of device ("WR" or "ER")
            sid: Shutter ID
            adr: Address of the shutter
            position: Position in percent (0 = open, 100 = closed)
            
        Returns:
            True if command was successful
        """
        if device_type == DEVICE_TYPE_WR:
            return self.set_wir_shutter_position(sid, adr, position)
        elif device_type == DEVICE_TYPE_ER:
            _LOGGER.warning("Elero shutters do not support position setting")
            return False
        else:
            _LOGGER.error("Unknown device type: %s", device_type)
            return False

    @staticmethod
    def parse_wir_position(state: str) -> int:
        """Parse position from WIR state string.
        
        The state format is "XXYYZZ" where YY and ZZ represent the position.
        Position 0 = fully open, 100 (0x64) = fully closed
        
        Args:
            state: State string from gateway (e.g., "010000", "016400", "014800")
            
        Returns:
            Position in percent (0-100)
        """
        if len(state) >= 6:
            # Extract bytes 2-3 (positions 2-5 in string)
            position_hex = state[2:4]
            try:
                position = int(position_hex, 16)
                return position
            except ValueError:
                _LOGGER.error("Could not parse WIR position from state: %s", state)
                return 0
        return 0

    @staticmethod
    def parse_elero_position(state: str) -> Optional[int]:
        """Parse position from Elero state string.
        
        Elero doesn't report exact positions, only states:
        - 1001: Fully open (0%)
        - 1002: Fully closed (100%)
        - 100D: Intermediate position (50%)
        - 100A: Moving up
        - 100B: Moving down
        
        Args:
            state: State string from gateway (e.g., "1001", "1002", "100D")
            
        Returns:
            Estimated position in percent (0-100) or None if moving
        """
        if state == ELERO_STATE_OPEN:
            return 0  # Fully open
        elif state == ELERO_STATE_CLOSED:
            return 100  # Fully closed
        elif state == ELERO_STATE_INTERMEDIATE:
            return 50  # Somewhere in between
        elif state in [ELERO_STATE_MOVING_UP, ELERO_STATE_MOVING_DOWN]:
            return None  # Moving, position unknown
        else:
            _LOGGER.warning("Unknown Elero state: %s", state)
            return None

    def parse_position(self, device_type: str, state: str) -> Optional[int]:
        """Parse position from state string based on device type.
        
        Args:
            device_type: Type of device ("WR" or "ER")
            state: State string from gateway
            
        Returns:
            Position in percent (0-100) or None if position unknown
        """
        if device_type == DEVICE_TYPE_WR:
            return self.parse_wir_position(state)
        elif device_type == DEVICE_TYPE_ER:
            return self.parse_elero_position(state)
        else:
            _LOGGER.error("Unknown device type: %s", device_type)
            return None

    def supports_position(self, device_type: str) -> bool:
        """Check if device type supports position setting.
        
        Args:
            device_type: Type of device ("WR" or "ER")
            
        Returns:
            True if device supports position setting
        """
        return device_type == DEVICE_TYPE_WR