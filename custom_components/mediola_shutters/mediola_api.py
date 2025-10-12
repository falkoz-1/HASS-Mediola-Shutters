"""API client for Mediola Gateway."""
import json
import logging
import requests
from typing import List, Dict, Any

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
            
            # Filter only shutter devices (type "WR")
            shutters = [d for d in devices if d.get("type") == "WR"]
            
            return shutters
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error fetching states from Mediola gateway: %s", err)
            raise
        except json.JSONDecodeError as err:
            _LOGGER.error("Error parsing response from Mediola gateway: %s", err)
            raise

    def send_command(self, adr: str, command: str) -> bool:
        """Send a command to a specific shutter.
        
        Args:
            adr: Address of the shutter (e.g., "2E105601")
            command: Command string to send
            
        Returns:
            True if command was successful
        """
        params = {
            "XC_FNC": "SendSC",
            "type": "WR",
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

    def open_shutter(self, sid: str, adr: str) -> bool:
        """Open a shutter completely.
        
        Args:
            sid: Shutter ID (e.g., "01", "02")
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010101
        command = f"01{adr}010101"
        return self.send_command(adr, command)

    def close_shutter(self, sid: str, adr: str) -> bool:
        """Close a shutter completely.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010102
        command = f"01{adr}010102"
        return self.send_command(adr, command)

    def stop_shutter(self, sid: str, adr: str) -> bool:
        """Stop a shutter.
        
        Args:
            sid: Shutter ID
            adr: Address of the shutter
            
        Returns:
            True if command was successful
        """
        # Command format: 01 + adr + 010103
        command = f"01{adr}010103"
        return self.send_command(adr, command)

    def set_shutter_position(self, sid: str, adr: str, position: int) -> bool:
        """Set shutter to a specific position.
        
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
        return self.send_command(adr, command)

    @staticmethod
    def parse_position_from_state(state: str) -> int:
        """Parse position from state string.
        
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
                _LOGGER.error("Could not parse position from state: %s", state)
                return 0
        return 0