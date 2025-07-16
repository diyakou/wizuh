from .xui import XUIAPI, XUIAPIError
import logging

logger = logging.getLogger(__name__)

class XUIClient:
    def __init__(self, url: str, username: str, password: str):
        """Initialize XUI client with server credentials."""
        self.api = XUIAPI(api_url=url, api_token=None)
        self.username = username
        self.password = password
        self.api.session.headers.pop("Authorization", None)

    def login(self) -> bool:
        """Login to XUI panel."""
        try:
            data = {
                "username": self.username,
                "password": self.password
            }
            response = self.api._make_request("POST", "/login", data)
            if response and response.get('success'):
                return True
            return False
        except XUIAPIError as e:
            logger.error(f"Login failed: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection and authentication to XUI panel."""
        return self.login()

    def get_server_stats(self) -> dict:
        """Get server statistics."""
        try:
            if not self.login():
                raise XUIAPIError("Authentication failed")
            return self.api.get_server_stats()
        except XUIAPIError as e:
            logger.error(f"Failed to get server stats: {e}")
            return {}
