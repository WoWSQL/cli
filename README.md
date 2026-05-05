# WoWSQL CLI

Command-line interface for managing WoWSQL backend services. A comprehensive CLI tool similar to wowsql CLI for managing databases, storage, migrations, and more.

## Installation

### From PyPI (Recommended)
```bash
pip install wowsql-cli
```

### From Source
```bash
cd cli
pip install -e .
```

**Note:** The CLI package is named `wowsql_cli` internally to avoid conflicts with the SDK's `wowsql` package, but the command is still `wowsql`.

## Quick Start

1. **Login:**
```bash
wowsql login
# Or with email
wowsql login --email your@email.com
```

2. **Initialize a project:**
```bash
wowsql init
# Or link to existing project
wowsql link your-project-slug
```

3. **List projects:**
```bash
wowsql projects list
```

4. **Set default project:**
```bash
wowsql projects set-default your-project-slug
```

5. **Query database:**
```bash
wowsql db query "SELECT * FROM users LIMIT 10"
```

## Commands

### Authentication

- `wowsql login [--email] [--api-key] [--profile]` - Login to WoWSQL
- `wowsql logout [--profile]` - Logout and clear credentials
- `wowsql auth status` - Show authentication status and current profile
- `wowsql auth switch-profile <name>` - Switch to a different profile

### Project Management

- `wowsql init [--project] [--template] [--force]` - Initialize a new WoWSQL project in current directory
- `wowsql projects list [--format]` - List all projects
- `wowsql projects get <slug>` - Get detailed project information
- `wowsql projects create <name> [--description] [--region]` - Create a new project
- `wowsql projects update <slug> [--name] [--description]` - Update project settings
- `wowsql projects delete <slug>` - Delete a project (⚠️ Permanent)
- `wowsql projects set-default <slug>` - Set the default project for commands
- `wowsql projects current` - Show the current default project
- `wowsql link <project-slug>` - Link current directory to a WoWSQL project
- `wowsql unlink` - Unlink current directory from project

### Database Operations

#### Table Management
- `wowsql db tables list [--project] [--format]` - List all tables in the database
- `wowsql db tables describe <table> [--project]` - Get table schema and column information

#### Query & Data Operations
- `wowsql db query "<sql>" [--file] [--project] [--format]` - Execute a SQL query
- `wowsql db insert <table> [--data] [--file] [--project]` - Insert data into a table
- `wowsql db update <table> --where "<condition>" --data '{"key": "value"}' [--project]` - Update data in a table
- `wowsql db delete <table> --where "<condition>" [--project]` - Delete data from a table

#### Import/Export
- `wowsql db export <table> [--output] [--format] [--project]` - Export table data to JSON or CSV
- `wowsql db import <table> --file <path> [--format] [--project]` - Import data from JSON or CSV file

#### Database Management
- `wowsql db dump [--output] [--schema-only] [--data-only] [--tables] [--project]` - Export entire database to SQL file
- `wowsql db restore --file <path> [--confirm] [--project]` - Restore database from SQL file
- `wowsql db seed [--file] [--project]` - Seed database with initial data from SQL or JSON file
- `wowsql db diff [--project] [--format]` - Compare local and remote database schemas
- `wowsql db connect [--project]` - Get database connection information

#### Schema Management
- `wowsql db schema dump [--output] [--project]` - Export database schema only (no data)
- `wowsql db schema diff [--project] [--format]` - Show schema differences between local and remote

#### Performance Tools
- `wowsql db explain "<sql>" [--project] [--format]` - Explain query execution plan
- `wowsql db analyze <table> [--project]` - Analyze table and update statistics
- `wowsql db optimize <table> [--project]` - Optimize table

### Database Objects

#### Views
- `wowsql views list [--project] [--format]` - List all database views
- `wowsql views create <name> [--file] "<sql>" [--project]` - Create a database view
- `wowsql views describe <name> [--project] [--format]` - Describe view structure

#### Stored Procedures
- `wowsql procedures list [--project] [--format]` - List all stored procedures
- `wowsql procedures create <name> [--file] "<sql>" [--project]` - Create a stored procedure
- `wowsql procedures execute <name> [--params] [--project] [--format]` - Execute a stored procedure

#### Indexes
- `wowsql indexes list [<table>] [--project] [--format]` - List indexes for a table or all tables
- `wowsql indexes create <name> <table> <columns> [--unique] [--project]` - Create an index on a table
- `wowsql indexes analyze <table> [--project] [--format]` - Analyze index usage for a table

#### Triggers
- `wowsql triggers list [<table>] [--project] [--format]` - List triggers for a table or all tables
- `wowsql triggers create <name> <table> <timing> <event> [--file] "<sql>" [--project]` - Create a database trigger
- `wowsql triggers delete <name> [--confirm] [--project]` - Delete a trigger

### Migrations

- `wowsql migration new <name> [--project]` - Create a new migration file
- `wowsql migration list [--project]` - List all migrations
- `wowsql migration status [--project]` - Show migration status (applied/pending)
- `wowsql migration up [--count] [--project]` - Apply pending migrations
- `wowsql migration down [--count] [--project]` - Rollback the last migration(s)

### Storage Operations

- `wowsql storage list [--prefix] [--project]` - List files in storage
- `wowsql storage upload <file> [--path] [--folder] [--project]` - Upload a file to storage
- `wowsql storage download <path> [--output] [--project]` - Download a file from storage
- `wowsql storage delete <path> [--project]` - Delete a file from storage
- `wowsql storage quota [--project]` - Check storage quota and usage

### Secrets Management

- `wowsql secrets list [--project] [--format]` - List all project secrets
- `wowsql secrets set <key> <value> [--public] [--project]` - Set a secret value
- `wowsql secrets get <key> [--project]` - Get a secret value
- `wowsql secrets unset <key> [--project]` - Delete a secret

### Logs & Monitoring

- `wowsql logs view [--follow] [--filter] [--limit] [--project] [--format]` - View project logs
- `wowsql status [--project] [--format]` - Show project status and health

### Backup & Restore

- `wowsql backup create [--name] [--project]` - Create a database backup
- `wowsql backup list [--project] [--format]` - List all backups for a project
- `wowsql backup restore <backup-id> [--confirm] [--project]` - Restore database from backup
- `wowsql backup download <backup-id> [--output] [--project]` - Download backup file

### Configuration Management

- `wowsql config get <key> [--project]` - Get a configuration value
- `wowsql config set <key> <value> [--project]` - Set a configuration value
- `wowsql config list [--project] [--format]` - List all configuration values

### Validation

- `wowsql validate [--project]` - Validate project configuration, database connection, schema, and migrations

### TypeScript Type Generation

- `wowsql gen typescript [--output] [--project]` - Generate TypeScript types from database schema

### Local Development

- `wowsql local start` - Start local development environment (Postgres, Redis, MinIO)
- `wowsql local stop` - Stop local development environment
- `wowsql local status` - Check status of local services
- `wowsql local reset` - Reset local environment (⚠️ Deletes all data)
- `wowsql local logs [--service] [--follow]` - View logs from local services

## Output Formats

Most commands support multiple output formats:

- `--output table` (default) - Human-readable table format
- `--output json` - JSON format for scripting
- `--output yaml` - YAML format

Example:
```bash
wowsql projects list --output json | jq '.[0].slug'
```

## Configuration

Configuration is stored in `~/.wowsql/config.yaml`. You can manage multiple profiles for different environments.

### Configuration File Structure
```yaml
api_url: https://api.wowsql.com
current_profile: default
profiles:
  default:
    api_url: https://api.wowsql.com
  production:
    api_url: https://api.wowsql.com
```

### Using Profiles
```bash
# Use a specific profile
wowsql --profile production projects list

# Switch default profile
wowsql auth switch-profile production
```

## Project Configuration

When you run `wowsql init` or `wowsql link`, a `.wowsql/config.yaml` file is created in your project directory. This allows commands to automatically use the linked project without specifying `--project` every time.

## Examples

### Complete Workflow
```bash
# 1. Login
wowsql login

# 2. Initialize project
wowsql init --template basic

# 3. Create a migration
wowsql migration new create_users_table

# 4. Edit the migration file in migrations/
# Then apply it
wowsql migration up

# 5. Seed the database
wowsql db seed --file seed.sql

# 6. Query the database
wowsql db query "SELECT * FROM users"

# 7. Create a backup
wowsql backup create --name "pre-deployment"

# 8. Generate TypeScript types
wowsql gen typescript --output src/types/database.ts
```

### Database Management
```bash
# Dump entire database
wowsql db dump --output backup.sql

# Dump schema only
wowsql db dump --schema-only --output schema.sql

# Restore from backup
wowsql db restore --file backup.sql --confirm

# Compare schemas
wowsql db diff
```

### Secrets Management
```bash
# Set a secret
wowsql secrets set API_KEY "sk_live_12345"

# Set a public secret (can be exposed to client)
wowsql secrets set STRIPE_KEY "pk_live_..." --public

# List all secrets
wowsql secrets list

# Get a secret value
wowsql secrets get API_KEY
```

### Performance Optimization
```bash
# Explain a query
wowsql db explain "SELECT * FROM users WHERE email = 'test@example.com'"

# Analyze table statistics
wowsql db analyze users

# Optimize table
wowsql db optimize users

# Analyze indexes
wowsql indexes analyze users
```

## Tips & Best Practices

1. **Set a Default Project**: Use `wowsql projects set-default <slug>` to avoid specifying `--project` in every command

2. **Use JSON Output for Scripts**: Pipe JSON output to `jq` or other tools for automation

3. **Link Projects**: Run `wowsql link` in your project directory to automatically use that project

4. **Use Profiles**: Create separate profiles for development, staging, and production environments

5. **Regular Backups**: Create backups before major changes:
   ```bash
   wowsql backup create --name "before-migration-$(date +%Y%m%d)"
   ```

6. **Validate Before Deploying**: Always run `wowsql validate` before deploying changes

## Troubleshooting

### Authentication Issues
```bash
# Check auth status
wowsql auth status

# Re-login if needed
wowsql logout
wowsql login
```

### Project Not Found
```bash
# List all projects
wowsql projects list

# Set default project
wowsql projects set-default <slug>

# Or use --project flag
wowsql db query "SELECT 1" --project <slug>
```

### Command Not Found
```bash
# Reinstall CLI
pip install --upgrade wowsql-cli

# Or from source
cd cli && pip install -e .
```

## Documentation

For complete documentation with detailed examples, see [docs.wowsql.com/cli](https://docs.wowsql.com/cli)

## Support

- GitHub Issues: [github.com/wowsql/cli/issues](https://github.com/wowsql/cli/issues)
- Documentation: [docs.wowsql.com](https://docs.wowsql.com)
- Email: support@wowsql.com

