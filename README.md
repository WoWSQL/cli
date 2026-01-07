# WoWSQL CLI

Command-line interface for managing WoWSQL backend services.

## Installation

```bash
cd cli
pip install -e .
```

Or install from PyPI (when available):
```bash
pip install wowsql-cli
```

**Note:** The CLI package is named `wowsql_cli` internally to avoid conflicts with the SDK's `wowsql` package, but the command is still `wowsql`.

## Quick Start

1. **Login:**
```bash
wowsql login
```

2. **List projects:**
```bash
wowsql projects list
```

3. **Set default project:**
```bash
wowsql projects set-default saravana-d92fd8e6
```

4. **Query database:**
```bash
wowsql db query "SELECT * FROM users LIMIT 10"
```

## Commands

### Authentication
- `wowsql login` - Login to WoWSQL
- `wowsql logout` - Logout
- `wowsql auth status` - Show authentication status

### Projects
- `wowsql projects list` - List all projects
- `wowsql projects create <name>` - Create new project
- `wowsql projects get <slug>` - Get project details
- `wowsql projects set-default <slug>` - Set default project

### Database
- `wowsql db tables list` - List all tables
- `wowsql db query "<sql>"` - Execute SQL query
- `wowsql db insert <table> --data '{"key": "value"}'` - Insert data
- `wowsql db export <table> --output data.json` - Export table data

### Migrations
- `wowsql migration new <name>` - Create new migration
- `wowsql migration up` - Apply pending migrations
- `wowsql migration down` - Rollback last migration
- `wowsql migration status` - Show migration status

### Storage
- `wowsql storage list` - List files
- `wowsql storage upload <file>` - Upload file
- `wowsql storage download <path>` - Download file

### Local Development
- `wowsql start` - Start local environment
- `wowsql stop` - Stop local environment
- `wowsql status` - Check services status

## Configuration

Configuration is stored in `~/.wowsql/config.yaml`. You can manage multiple profiles for different environments.

## Documentation

For complete documentation, see [docs.wowsql.com/cli](https://docs.wowsql.com/cli)

