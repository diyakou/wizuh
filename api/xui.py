import requests
from config.settings import XUI_API_URL, XUI_API_TOKEN
import logging
from typing import Dict, List, Optional, Union
import json
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class XUIAPIError(Exception):
    """Custom exception for XUI API errors."""
    pass

class XUIAPI:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to XUI API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data (for POST/PUT)
            
        Returns:
            dict: Response data
            
        Raises:
            XUIAPIError: If request fails
        """
        try:
            url = f"{self.api_url}{endpoint}"
            
            response = self.session.request(method, url, json=data)
            response.raise_for_status()
            
            # Handle empty response
            if response.text:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"XUI API request failed: {e}")
            raise XUIAPIError(f"Error communicating with XUI panel: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise XUIAPIError(f"Invalid JSON response from XUI panel: {response.text}")

    def get_server_stats(self) -> Dict:
        """Get server statistics."""
        return self._make_request("GET", "/server/status")