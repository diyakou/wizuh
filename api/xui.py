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
    def __init__(self, api_url: str = XUI_API_URL, api_token: str = XUI_API_TOKEN):
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
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
            url = f"{self.api_url}/{endpoint.lstrip('/')}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"XUI API request failed: {e}")
            raise XUIAPIError(f"Error communicating with XUI panel: {e}")
    
    def create_client(self, protocol: str, email: str, uuid: str = None) -> Dict:
        """
        Create a new client configuration.
        
        Args:
            protocol: Protocol type (vless, vmess, trojan)
            email: Client email/identifier
            uuid: Optional UUID (auto-generated if not provided)
            
        Returns:
            dict: Client configuration
        """
        data = {
            "protocol": protocol,
            "email": email
        }
        if uuid:
            data["uuid"] = uuid
            
        return self._make_request("POST", "/client", data)
    
    def get_client(self, client_id: str) -> Dict:
        """Get client configuration by ID."""
        return self._make_request("GET", f"/client/{client_id}")
    
    def update_client(self, client_id: str, **kwargs) -> Dict:
        """Update client configuration."""
        return self._make_request("PUT", f"/client/{client_id}", kwargs)
    
    def delete_client(self, client_id: str) -> Dict:
        """Delete client configuration."""
        return self._make_request("DELETE", f"/client/{client_id}")
    
    def get_server_stats(self) -> Dict:
        """Get server statistics."""
        return self._make_request("GET", "/stats")
    
    def get_client_traffic(self, client_id: str) -> Dict:
        """Get client traffic statistics."""
        return self._make_request("GET", f"/client/{client_id}/traffic")
    
    def generate_config_link(self, client_id: str, protocol: str) -> str:
        """
        Generate configuration link for client.
        
        Args:
            client_id: Client ID
            protocol: Protocol type (vless, vmess, trojan)
            
        Returns:
            str: Configuration link
        """
        client = self.get_client(client_id)
        
        if protocol == "vless":
            return self._generate_vless_link(client)
        elif protocol == "vmess":
            return self._generate_vmess_link(client)
        elif protocol == "trojan":
            return self._generate_trojan_link(client)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    def _generate_vless_link(self, client: Dict) -> str:
        """Generate VLESS configuration link."""
        params = {
            "type": "tcp",
            "encryption": "none",
            "flow": client.get("flow", ""),
            "security": client.get("security", "none")
        }
        
        if params["security"] == "tls":
            params.update({
                "sni": client.get("sni", ""),
                "fp": client.get("fingerprint", ""),
                "alpn": client.get("alpn", "")
            })
        
        params_str = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"vless://{client['uuid']}@{client['address']}:{client['port']}?{params_str}#{client['email']}"
    
    def _generate_vmess_link(self, client: Dict) -> str:
        """Generate VMess configuration link."""
        config = {
            "v": "2",
            "ps": client["email"],
            "add": client["address"],
            "port": client["port"],
            "id": client["uuid"],
            "aid": client.get("alterId", 0),
            "net": client.get("network", "tcp"),
            "type": client.get("type", "none"),
            "host": client.get("host", ""),
            "path": client.get("path", ""),
            "tls": client.get("security", "none")
        }
        
        if config["tls"] == "tls":
            config.update({
                "sni": client.get("sni", ""),
                "alpn": client.get("alpn", "")
            })
        
        return f"vmess://{json.dumps(config)}"
    
    def _generate_trojan_link(self, client: Dict) -> str:
        """Generate Trojan configuration link."""
        params = {
            "security": client.get("security", "tls"),
            "type": client.get("type", "tcp"),
            "host": client.get("host", ""),
            "path": client.get("path", ""),
            "sni": client.get("sni", "")
        }
        
        params_str = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"trojan://{client['password']}@{client['address']}:{client['port']}?{params_str}#{client['email']}"

class XUIClient:
    def __init__(self, url: str, username: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None):
        """Initialize X-UI client with either username/password or token.
        
        Args:
            url: The base URL of the X-UI panel
            username: Optional username for authentication
            password: Optional password for authentication
            token: Optional API token for authentication
        """
        self.base_url = url.rstrip('/')
        self.username = username
        self.password = password
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def check_connection(self) -> bool:
        """Check if connection to X-UI panel is working."""
        try:
            if self.token:
                response = self.session.get(f"{self.base_url}/api/status")
            else:
                response = self.session.post(
                    f"{self.base_url}/login",
                    json={"username": self.username, "password": self.password}
                )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return False
    
    def create_config(
        self,
        protocol: str,
        email: str,
        total_gb: int,
        expiry_days: int,
        inbound_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Create a new V2Ray config.
        
        Args:
            protocol: The protocol to use (vmess, vless, trojan)
            email: User email/identifier
            total_gb: Total GB allowed
            expiry_days: Number of days until expiry
            inbound_id: Optional inbound ID to use
            
        Returns:
            Dict containing config details if successful, None otherwise
        """
        try:
            data = {
                "protocol": protocol,
                "email": email,
                "total_gb": total_gb,
                "expiry_days": expiry_days
            }
            if inbound_id:
                data["inbound_id"] = inbound_id
            
            response = self.session.post(f"{self.base_url}/api/config", json=data)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error creating config: {e}")
            return None
    
    def delete_config(self, uuid: str, inbound_id: int) -> bool:
        """Delete a V2Ray config.
        
        Args:
            uuid: The UUID of the config to delete
            inbound_id: The inbound ID of the config
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/config/{inbound_id}/{uuid}"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting config: {e}")
            return False
    
    def update_config(
        self,
        uuid: str,
        inbound_id: int,
        total_gb: int,
        expiry_days: int
    ) -> bool:
        """Update a V2Ray config.
        
        Args:
            uuid: The UUID of the config to update
            inbound_id: The inbound ID of the config
            total_gb: New total GB allowed
            expiry_days: New number of days until expiry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "total_gb": total_gb,
                "expiry_days": expiry_days
            }
            response = self.session.put(
                f"{self.base_url}/api/config/{inbound_id}/{uuid}",
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False
    
    def get_config_status(self, uuid: str, inbound_id: int) -> Optional[Dict]:
        """Get status of a V2Ray config.
        
        Args:
            uuid: The UUID of the config
            inbound_id: The inbound ID of the config
            
        Returns:
            Dict containing status if successful, None otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/config/{inbound_id}/{uuid}/status"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting config status: {e}")
            return None
    
    def get_server_status(self) -> Optional[Dict]:
        """Get server status information.
        
        Returns:
            Dict containing server status if successful, None otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return None 