"""Configuration management for WoWSQL CLI."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64
import hashlib

from wowsql_cli.exceptions import ConfigurationError


class Config:
    """Manages CLI configuration and profiles."""
    
    def __init__(self, profile: Optional[str] = None):
        self.config_dir = Path.home() / ".wowsql"
        self.config_file = self.config_dir / "config.yaml"
        self.credentials_file = self.config_dir / "credentials.enc"
        self.profile = profile
        self._config = {}
        self._credentials = {}
        self._encryption_key = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._load_config()
        self._load_credentials()
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key for credentials."""
        key_file = self.config_dir / ".key"
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            # Generate new key
            self._encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            # Set restrictive permissions (Unix only)
            if os.name != 'nt':
                os.chmod(key_file, 0o600)
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self._encryption_key:
            self._init_encryption_key()
        f = Fernet(self._encryption_key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self._encryption_key:
            self._init_encryption_key()
        try:
            f = Fernet(self._encryption_key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            # If decryption fails, the key might have changed
            raise ConfigurationError(f"Failed to decrypt credentials: {e}. You may need to login again.")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                raise ConfigurationError(f"Failed to load config: {e}")
        else:
            self._config = {
                'api_url': 'https://api.wowsql.com',
                'current_profile': 'default',
                'profiles': {}
            }
            self._save_config()
    
    def _save_config(self):
        """Save configuration to YAML file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            # Set restrictive permissions (Unix only)
            if os.name != 'nt':
                os.chmod(self.config_file, 0o600)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    def _load_credentials(self):
        """Load encrypted credentials."""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    encrypted = f.read()
                    if encrypted.strip():  # Only try to decrypt if file has content
                        decrypted = self._decrypt(encrypted)
                        self._credentials = yaml.safe_load(decrypted) or {}
                    else:
                        self._credentials = {}
            except Exception as e:
                # If decryption fails, log the error but don't crash
                # This might happen if encryption key changed or file is corrupted
                import logging
                logging.debug(f"Failed to load credentials: {e}")
                self._credentials = {}
        else:
            self._credentials = {}
    
    def _save_credentials(self):
        """Save encrypted credentials."""
        try:
            encrypted = self._encrypt(yaml.dump(self._credentials))
            with open(self.credentials_file, 'w') as f:
                f.write(encrypted)
            # Set restrictive permissions (Unix only)
            if os.name != 'nt':
                os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            raise ConfigurationError(f"Failed to save credentials: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        profile_name = self.profile or self._config.get('current_profile', 'default')
        profile = self._config.get('profiles', {}).get(profile_name, {})
        
        # Check profile first, then global config
        if key in profile:
            return profile[key]
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any, profile: Optional[str] = None):
        """Set configuration value."""
        profile_name = profile or self.profile or self._config.get('current_profile', 'default')
        
        if 'profiles' not in self._config:
            self._config['profiles'] = {}
        if profile_name not in self._config['profiles']:
            self._config['profiles'][profile_name] = {}
        
        self._config['profiles'][profile_name][key] = value
        self._save_config()
    
    def get_api_key(self, profile: Optional[str] = None) -> Optional[str]:
        """Get API key for profile."""
        # Reload credentials to ensure we have the latest
        self._load_credentials()
        profile_name = profile or self.profile or self._config.get('current_profile', 'default')
        return self._credentials.get(profile_name, {}).get('api_key')
    
    def set_api_key(self, api_key: str, profile: Optional[str] = None):
        """Set API key for profile."""
        profile_name = profile or self.profile or self._config.get('current_profile', 'default')
        
        if profile_name not in self._credentials:
            self._credentials[profile_name] = {}
        
        self._credentials[profile_name]['api_key'] = api_key
        self._save_credentials()
    
    def get_api_url(self) -> str:
        """Get API URL."""
        return self.get('api_url', 'https://api.wowsql.com')
    
    def get_default_project(self) -> Optional[str]:
        """Get default project slug."""
        return self.get('default_project')
    
    def set_default_project(self, project_slug: str, profile: Optional[str] = None):
        """Set default project slug."""
        self.set('default_project', project_slug, profile)
    
    def list_profiles(self) -> list:
        """List all profiles."""
        return list(self._config.get('profiles', {}).keys())
    
    def create_profile(self, name: str, api_url: Optional[str] = None):
        """Create a new profile."""
        if 'profiles' not in self._config:
            self._config['profiles'] = {}
        
        self._config['profiles'][name] = {
            'api_url': api_url or self.get_api_url()
        }
        self._save_config()
    
    def delete_profile(self, name: str):
        """Delete a profile."""
        if name in self._config.get('profiles', {}):
            del self._config['profiles'][name]
            if self._config.get('current_profile') == name:
                self._config['current_profile'] = 'default'
            self._save_config()
        
        if name in self._credentials:
            del self._credentials[name]
            self._save_credentials()
    
    def set_current_profile(self, name: str):
        """Set current active profile."""
        if name not in self._config.get('profiles', {}):
            raise ConfigurationError(f"Profile '{name}' does not exist")
        self._config['current_profile'] = name
        self._save_config()
    
    def get_current_profile(self) -> str:
        """Get current active profile."""
        return self._config.get('current_profile', 'default')
    
    def get_project_config(self, project_dir: Path) -> Optional[Dict[str, Any]]:
        """Load project-specific configuration."""
        project_config_file = project_dir / ".wowsql" / "config.yaml"
        if project_config_file.exists():
            try:
                with open(project_config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception:
                return None
        return None
    
    def save_project_config(self, project_dir: Path, config: Dict[str, Any]):
        """Save project-specific configuration."""
        project_config_dir = project_dir / ".wowsql"
        project_config_dir.mkdir(parents=True, exist_ok=True)
        project_config_file = project_config_dir / "config.yaml"
        
        with open(project_config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

