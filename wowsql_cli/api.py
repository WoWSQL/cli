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
    
    # Storage methods — wire to real storage API
    # Real paths: /storage/projects/{slug}/buckets/{bucket}/files
    # The CLI treats "storage" as a flat file system; we map to the default bucket.

    DEFAULT_BUCKET = "default"

    def list_storage(self, project_slug: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List storage files in the default bucket."""
        params = {}
        if prefix:
            params['prefix'] = prefix
        return self._request(
            'GET',
            f'/storage/projects/{project_slug}/buckets/{self.DEFAULT_BUCKET}/files',
            params=params,
        )

    def upload_file(self, project_slug: str, file_path: Path, remote_path: str) -> Dict[str, Any]:
        """Upload file to storage (default bucket)."""
        import mimetypes
        mime, _ = mimetypes.guess_type(str(file_path))
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, mime or 'application/octet-stream')}
            data = {'path': remote_path}
            # multipart upload — do NOT set Content-Type header (requests sets it with boundary)
            saved_ct = self.session.headers.pop('Content-Type', None)
            try:
                response = self.session.post(
                    f"{self.base_url}/storage/projects/{project_slug}/buckets/{self.DEFAULT_BUCKET}/files",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                return response.json()
            finally:
                if saved_ct:
                    self.session.headers['Content-Type'] = saved_ct

    def download_file(self, project_slug: str, remote_path: str, local_path: Path):
        """Download file from storage."""
        encoded = remote_path.lstrip('/')
        response = self.session.get(
            f"{self.base_url}/storage/projects/{project_slug}/files/{encoded}",
        )
        response.raise_for_status()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(response.content)

    def delete_file(self, project_slug: str, remote_path: str) -> Dict[str, Any]:
        """Delete file from storage."""
        encoded = remote_path.lstrip('/')
        return self._request(
            'DELETE',
            f'/storage/projects/{project_slug}/files/{encoded}',
        )
    
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
    
    def rollback_migration(self, project_slug: str, migration_name: str,
                          down_sql: Optional[str] = None) -> Dict[str, Any]:
        """Rollback a migration, optionally executing its DOWN SQL."""
        payload: Dict[str, Any] = {'name': migration_name}
        if down_sql:
            payload['down_sql'] = down_sql
        return self._request('POST', '/api/v1/migration/rollback',
                           json=payload,
                           headers={'X-Project-Slug': project_slug})
    
    # Logs and monitoring methods
    def get_logs(self, project_slug: str, filter: Optional[str] = None, 
                 limit: int = 100, follow: bool = False) -> List[Dict[str, Any]]:
        """Get project logs."""
        params = {'limit': limit}
        if filter:
            params['filter'] = filter
        if follow:
            params['follow'] = 'true'
        return self._request('GET', '/api/v1/logs',
                           params=params,
                           headers={'X-Project-Slug': project_slug})
    
    def get_project_status(self, project_slug: str) -> Dict[str, Any]:
        """Get project status and health."""
        return self._request('GET', '/api/v1/projects/{}/status'.format(project_slug))
    
    # Database dump/restore methods
    def dump_database(self, project_slug: str, schema_only: bool = False,
                     data_only: bool = False, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Dump database to SQL."""
        data = {
            'schema_only': schema_only,
            'data_only': data_only
        }
        if tables:
            data['tables'] = tables
        return self._request('POST', '/api/v1/db/dump',
                           json=data,
                           headers={'X-Project-Slug': project_slug})
    
    def restore_database(self, project_slug: str, sql: str) -> Dict[str, Any]:
        """Restore database from SQL (legacy JSON endpoint)."""
        return self._request('POST', '/api/v1/db/restore',
                           json={'sql': sql},
                           headers={'X-Project-Slug': project_slug})

    def restore_from_file(self, project_slug: str, sql: str,
                          skip_errors: bool = False) -> Dict[str, Any]:
        """Upload a local .sql file's content and restore the remote database."""
        return self._request('POST', '/api/v1/db/restore-file',
                           json={'sql': sql, 'skip_errors': skip_errors},
                           headers={'X-Project-Slug': project_slug})

    def import_csv_table(self, project_slug: str, table: str, csv_content: str,
                         delimiter: str = ',', has_header: bool = True,
                         create_table: bool = False,
                         on_conflict: str = 'error') -> Dict[str, Any]:
        """Send local CSV content to the server for import into a table."""
        return self._request(
            'POST', '/api/v1/db/import-csv',
            json={
                'table': table,
                'csv_content': csv_content,
                'delimiter': delimiter,
                'has_header': has_header,
                'create_table': create_table,
                'on_conflict': on_conflict,
            },
            headers={'X-Project-Slug': project_slug},
        )
    
    def compare_schemas(self, project_slug: str, local_schema: Dict[str, Any],
                       remote_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Compare local and remote schemas."""
        return self._request('POST', '/api/v1/db/schema/diff',
                           json={'local': local_schema, 'remote': remote_schema},
                           headers={'X-Project-Slug': project_slug})
    
    def get_database_connection(self, project_slug: str) -> Dict[str, Any]:
        """Get database connection information."""
        return self._request('GET', '/api/v1/db/connection',
                           headers={'X-Project-Slug': project_slug})
    
    # Backup methods
    def create_backup(self, project_slug: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a database backup."""
        data = {}
        if name:
            data['name'] = name
        return self._request('POST', '/api/v1/backups/',
                           json=data,
                           headers={'X-Project-Slug': project_slug})
    
    def list_backups(self, project_slug: str) -> List[Dict[str, Any]]:
        """List all backups for a project."""
        return self._request('GET', '/api/v1/backups/',
                           headers={'X-Project-Slug': project_slug})
    
    def restore_backup(self, project_slug: str, backup_id: str) -> Dict[str, Any]:
        """Restore database from backup."""
        return self._request('POST', f'/api/v1/backups/{backup_id}/restore',
                           headers={'X-Project-Slug': project_slug})
    
    def download_backup(self, project_slug: str, backup_id: str, output_path: Path):
        """Download backup file."""
        response = self.session.get(
            f"{self.base_url}/api/v1/backups/{backup_id}/download",
            headers={'X-Project-Slug': project_slug}
        )
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
    
    # Config methods
    def get_config(self, project_slug: str, key: str) -> Any:
        """Get a configuration value."""
        return self._request('GET', f'/api/v1/config/{key}',
                           headers={'X-Project-Slug': project_slug})
    
    def set_config(self, project_slug: str, key: str, value: str) -> Dict[str, Any]:
        """Set a configuration value."""
        return self._request('PUT', f'/api/v1/config/{key}',
                           json={'value': value},
                           headers={'X-Project-Slug': project_slug})
    
    def list_config(self, project_slug: str) -> Dict[str, Any]:
        """List all configuration values."""
        return self._request('GET', '/api/v1/config/',
                           headers={'X-Project-Slug': project_slug})
    
    # Secrets methods (complete implementation)
    def list_secrets(self, project_slug: str) -> List[Dict[str, Any]]:
        """List all secrets."""
        return self._request('GET', f'/api/v1/secrets/projects/{project_slug}')
    
    def set_secret(self, project_slug: str, key: str, value: str, is_public: bool = False) -> Dict[str, Any]:
        """Set a secret value."""
        return self._request('POST', f'/api/v1/secrets/projects/{project_slug}',
                           json={'key': key, 'value': value, 'is_public': is_public})
    
    def get_secret(self, project_slug: str, key: str) -> str:
        """Get a secret value."""
        result = self._request('GET', f'/api/v1/secrets/projects/{project_slug}/{key}')
        return result.get('value', '')
    
    def delete_secret(self, project_slug: str, key: str) -> Dict[str, Any]:
        """Delete a secret."""
        return self._request('DELETE', f'/api/v1/secrets/projects/{project_slug}/{key}')
    
    # Storage quota
    def get_storage_quota(self, project_slug: str) -> Dict[str, Any]:
        """Get storage quota information."""
        return self._request('GET', '/api/v1/storage/quota',
                           headers={'X-Project-Slug': project_slug})
    
    # Views methods
    def list_views(self, project_slug: str) -> List[Dict[str, Any]]:
        """List all database views."""
        return self._request('GET', '/api/v1/db/views',
                           headers={'X-Project-Slug': project_slug})
    
    def create_view(self, project_slug: str, view_name: str, sql: str) -> Dict[str, Any]:
        """Create a database view."""
        return self._request('POST', '/api/v1/db/views',
                           json={'name': view_name, 'sql': sql},
                           headers={'X-Project-Slug': project_slug})
    
    def describe_view(self, project_slug: str, view_name: str) -> Dict[str, Any]:
        """Get view structure."""
        return self._request('GET', f'/api/v1/db/views/{view_name}',
                           headers={'X-Project-Slug': project_slug})
    
    # Procedures methods
    def list_procedures(self, project_slug: str) -> List[Dict[str, Any]]:
        """List all stored procedures."""
        return self._request('GET', '/api/v1/db/procedures',
                           headers={'X-Project-Slug': project_slug})
    
    def create_procedure(self, project_slug: str, procedure_name: str, sql: str) -> Dict[str, Any]:
        """Create a stored procedure."""
        return self._request('POST', '/api/v1/db/procedures',
                           json={'name': procedure_name, 'sql': sql},
                           headers={'X-Project-Slug': project_slug})
    
    def execute_procedure(self, project_slug: str, procedure_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a stored procedure."""
        return self._request('POST', f'/api/v1/db/procedures/{procedure_name}/execute',
                           json={'params': params},
                           headers={'X-Project-Slug': project_slug})
    
    # Indexes methods
    def list_indexes(self, project_slug: str, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """List indexes for a table or all tables."""
        params = {}
        if table:
            params['table'] = table
        return self._request('GET', '/api/v1/db/indexes',
                           params=params,
                           headers={'X-Project-Slug': project_slug})
    
    def create_index(self, project_slug: str, table: str, index_name: str, 
                    columns: List[str], unique: bool = False) -> Dict[str, Any]:
        """Create an index."""
        return self._request('POST', '/api/v1/db/indexes',
                           json={'table': table, 'name': index_name, 'columns': columns, 'unique': unique},
                           headers={'X-Project-Slug': project_slug})
    
    def analyze_indexes(self, project_slug: str, table: str) -> Dict[str, Any]:
        """Analyze index usage."""
        return self._request('GET', f'/api/v1/db/indexes/analyze',
                           params={'table': table},
                           headers={'X-Project-Slug': project_slug})
    
    # Triggers methods
    def list_triggers(self, project_slug: str, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """List triggers for a table or all tables."""
        params = {}
        if table:
            params['table'] = table
        return self._request('GET', '/api/v1/db/triggers',
                           params=params,
                           headers={'X-Project-Slug': project_slug})
    
    def create_trigger(self, project_slug: str, trigger_name: str, table: str,
                      timing: str, event: str, body: str) -> Dict[str, Any]:
        """Create a trigger."""
        return self._request('POST', '/api/v1/db/triggers',
                           json={'name': trigger_name, 'table': table, 'timing': timing, 
                                'event': event, 'body': body},
                           headers={'X-Project-Slug': project_slug})
    
    def delete_trigger(self, project_slug: str, trigger_name: str) -> Dict[str, Any]:
        """Delete a trigger."""
        return self._request('DELETE', f'/api/v1/db/triggers/{trigger_name}',
                           headers={'X-Project-Slug': project_slug})
    
    # Performance methods
    def explain_query(self, project_slug: str, sql: str) -> Dict[str, Any]:
        """Explain query execution plan."""
        return self._request('POST', '/api/v1/db/explain',
                           json={'query': sql},
                           headers={'X-Project-Slug': project_slug})
    
    def analyze_table(self, project_slug: str, table: str) -> Dict[str, Any]:
        """Analyze table and update statistics."""
        return self._request('POST', f'/api/v1/db/tables/{table}/analyze',
                           headers={'X-Project-Slug': project_slug})
    
    def optimize_table(self, project_slug: str, table: str) -> Dict[str, Any]:
        """Optimize table."""
        return self._request('POST', f'/api/v1/db/tables/{table}/optimize',
                           headers={'X-Project-Slug': project_slug})

