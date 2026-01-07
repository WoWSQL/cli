"""API client for WoWSQL backend."""

import requests
from typing import Dict, Any, Optional, List
from pathlib import Path

from wowsql_cli.config import Config
from wowsql_cli.auth import AuthManager
from wowsql_cli.exceptions import APIError, AuthenticationError


class APIClient:
    """Client for making requests to WoWSQL API."""
    
    def __init__(self, config: Config, auth_manager: AuthManager):
        self.config = config
        self.auth = auth_manager
        self.base_url = config.get_api_url()
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with authentication."""
        # Force reload credentials in case they were saved in a different process
        self.config._load_credentials()
        api_key = self.auth.get_api_key()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
        else:
            # Remove auth header if no key
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        
        # Ensure headers are up to date
        self._update_headers()
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please run 'wowsql login'")
            
            # Handle other errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_data.get('message', 'Unknown error'))
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                raise APIError(f"API Error: {error_msg}")
            
            # Return JSON response
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")
    
    # Project methods
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        return self._request('GET', '/api/v1/projects/')
    
    def get_project(self, slug: str) -> Dict[str, Any]:
        """Get project details."""
        return self._request('GET', f'/api/v1/projects/{slug}')
    
    def create_project(self, name: str, db_password: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create a new project."""
        data = {'name': name, **kwargs}
        if db_password:
            data['db_password'] = db_password
        return self._request('POST', '/api/v1/projects/', json=data)
    
    def update_project(self, slug: str, **kwargs) -> Dict[str, Any]:
        """Update project."""
        return self._request('PUT', f'/api/v1/projects/{slug}', json=kwargs)
    
    def delete_project(self, slug: str) -> Dict[str, Any]:
        """Delete project."""
        return self._request('DELETE', f'/api/v1/projects/{slug}')
    
    # Database methods
    def list_tables(self, project_slug: str) -> List[str]:
        """List all tables in project."""
        return self._request('GET', '/api/v1/db/tables', 
                           headers={'X-Project-Slug': project_slug})
    
    def describe_table(self, project_slug: str, table_name: str) -> Dict[str, Any]:
        """Get table schema."""
        return self._request('GET', f'/api/v1/db/tables/{table_name}',
                           headers={'X-Project-Slug': project_slug})
    
    def query(self, project_slug: str, sql: str) -> Dict[str, Any]:
        """Execute SQL query."""
        return self._request('POST', '/api/v1/db/execute',
                           json={'query': sql},
                           headers={'X-Project-Slug': project_slug})
    
    def insert_data(self, project_slug: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into table."""
        return self._request('POST', f'/api/v1/db/tables/{table_name}',
                           json=data,
                           headers={'X-Project-Slug': project_slug})
    
    def update_data(self, project_slug: str, table_name: str, where: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in table."""
        return self._request('PUT', f'/api/v1/db/tables/{table_name}',
                           json={'where': where, 'data': data},
                           headers={'X-Project-Slug': project_slug})
    
    def delete_data(self, project_slug: str, table_name: str, where: str) -> Dict[str, Any]:
        """Delete data from table."""
        return self._request('DELETE', f'/api/v1/db/tables/{table_name}',
                           params={'where': where},
                           headers={'X-Project-Slug': project_slug})
    
    # Storage methods
    def list_storage(self, project_slug: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List storage files."""
        params = {}
        if prefix:
            params['prefix'] = prefix
        return self._request('GET', '/api/v1/storage/',
                           params=params,
                           headers={'X-Project-Slug': project_slug})
    
    def upload_file(self, project_slug: str, file_path: Path, remote_path: str) -> Dict[str, Any]:
        """Upload file to storage."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'path': remote_path}
            return self._request('POST', '/api/v1/storage/upload',
                               files=files, data=data,
                               headers={'X-Project-Slug': project_slug})
    
    def download_file(self, project_slug: str, remote_path: str, local_path: Path):
        """Download file from storage."""
        response = self.session.get(
            f"{self.base_url}/api/v1/storage/download",
            params={'path': remote_path},
            headers={'X-Project-Slug': project_slug}
        )
        response.raise_for_status()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(response.content)
    
    def delete_file(self, project_slug: str, remote_path: str) -> Dict[str, Any]:
        """Delete file from storage."""
        return self._request('DELETE', '/api/v1/storage/',
                           params={'path': remote_path},
                           headers={'X-Project-Slug': project_slug})
    
    # Schema methods
    def get_schema(self, project_slug: str) -> Dict[str, Any]:
        """Get database schema."""
        return self._request('GET', '/api/v2/schema/tables',
                           headers={'X-Project-Slug': project_slug})
    
    def get_table_schema(self, project_slug: str, table_name: str) -> Dict[str, Any]:
        """Get table schema details."""
        return self._request('GET', f'/api/v2/schema/tables/{table_name}',
                           headers={'X-Project-Slug': project_slug})
    
    # Migration methods
    def get_migration_history(self, project_slug: str) -> List[Dict[str, Any]]:
        """Get migration history."""
        return self._request('GET', '/api/v1/migration/history',
                           headers={'X-Project-Slug': project_slug})
    
    def apply_migration(self, project_slug: str, migration_name: str, sql: str) -> Dict[str, Any]:
        """Apply a migration."""
        return self._request('POST', '/api/v1/migration/apply',
                           json={'name': migration_name, 'sql': sql},
                           headers={'X-Project-Slug': project_slug})
    
    def rollback_migration(self, project_slug: str, migration_name: str) -> Dict[str, Any]:
        """Rollback a migration."""
        return self._request('POST', '/api/v1/migration/rollback',
                           json={'name': migration_name},
                           headers={'X-Project-Slug': project_slug})

