"""Authentication handling for WoWSQL CLI."""

import keyring
import getpass
from typing import Optional, Dict, Any
import requests
from rich.console import Console
from rich.prompt import Prompt

from wowsql_cli.config import Config
from wowsql_cli.exceptions import AuthenticationError

console = Console()


class AuthManager:
    """Manages authentication for WoWSQL CLI."""
    
    SERVICE_NAME = "wowsql-cli"
    
    def __init__(self, config: Config):
        self.config = config
        self._token_cache = {}
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None, 
              api_key: Optional[str] = None, profile: Optional[str] = None) -> bool:
        """Login to WoWSQL API."""
        profile_name = profile or self.config.get_current_profile()
        
        # If API key provided, use it directly
        if api_key:
            self.config.set_api_key(api_key, profile_name)
            # Verify the API key works
            if self._verify_api_key(api_key):
                console.print(f"[green]✓[/green] Logged in successfully (profile: {profile_name})")
                return True
            else:
                raise AuthenticationError("Invalid API key")
        
        # Otherwise, use email/password
        if not email:
            email = Prompt.ask("Email")
        
        if not password:
            password = getpass.getpass("Password: ")
        
        # Authenticate with API
        api_url = self.config.get_api_url()
        try:
            response = requests.post(
                f"{api_url}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Store API key - login returns access_token in Token response
            api_key = data.get('access_token')
            if not api_key:
                # Try alternative field names
                api_key = data.get('api_key') or data.get('token')
                if not api_key:
                    # Debug: show what we got (but don't show full response for security)
                    console.print(f"[yellow]Warning:[/yellow] Login response keys: {list(data.keys())}")
                    raise AuthenticationError("No access_token in login response. Please check your API endpoint.")
            
            self.config.set_api_key(api_key, profile_name)
            
            # Verify it was saved
            saved_key = self.config.get_api_key(profile_name)
            if saved_key != api_key:
                console.print(f"[yellow]Warning:[/yellow] API key may not have been saved correctly")
            
            # Also store email in keyring for convenience
            keyring.set_password(
                self.SERVICE_NAME,
                f"{profile_name}:email",
                email
            )
            
            console.print(f"[green]✓[/green] Logged in successfully (profile: {profile_name})")
            return True
            
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Login failed: {e}")
    
    def logout(self, profile: Optional[str] = None):
        """Logout and clear credentials."""
        profile_name = profile or self.config.get_current_profile()
        
        # Clear API key
        if profile_name in self.config._credentials:
            del self.config._credentials[profile_name]
            self.config._save_credentials()
        
        # Clear keyring
        try:
            keyring.delete_password(self.SERVICE_NAME, f"{profile_name}:email")
        except keyring.errors.PasswordDeleteError:
            pass
        
        console.print(f"[green]✓[/green] Logged out (profile: {profile_name})")
    
    def get_api_key(self, profile: Optional[str] = None) -> Optional[str]:
        """Get API key for current profile."""
        return self.config.get_api_key(profile)
    
    def is_authenticated(self, profile: Optional[str] = None) -> bool:
        """Check if user is authenticated."""
        api_key = self.get_api_key(profile)
        if not api_key:
            return False
        return self._verify_api_key(api_key)
    
    def _verify_api_key(self, api_key: str) -> bool:
        """Verify API key is valid by making a test request."""
        api_url = self.config.get_api_url()
        try:
            response = requests.get(
                f"{api_url}/api/v1/projects/",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_status(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """Get authentication status."""
        profile_name = profile or self.config.get_current_profile()
        api_key = self.get_api_key(profile_name)
        is_auth = self.is_authenticated(profile_name) if api_key else False
        
        return {
            'profile': profile_name,
            'authenticated': is_auth,
            'api_url': self.config.get_api_url(),
            'has_api_key': api_key is not None
        }

