from .xui import XUIAPI
import logging

logger = logging.getLogger(__name__)

class XUIClient(XUIAPI):
    def __init__(self, url: str, username: str, password: str):
        """Initialize XUI client with server credentials."""
        super().__init__(api_url=url)
        self.username = username
        self.password = password
        
    def login(self) -> bool:
        """Login to XUI panel."""
        try:
            data = {
                "username": self.username,
                "password": self.password
            }
            self._make_request("POST", "/login", data)
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection and authentication to XUI panel."""
        try:
            return self.login()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_server_stats(self) -> dict:
        """Get server statistics."""
        try:
            if not self.login():
                raise Exception("Authentication failed")
            return super().get_server_stats()
        except Exception as e:
            logger.error(f"Failed to get server stats: {e}")
            return {
                "active_users": 0,
                "total_traffic": 0,
                "today_traffic": 0
            }
