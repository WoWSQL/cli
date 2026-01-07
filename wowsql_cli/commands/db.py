"""Database operation commands."""

import click
import json
from pathlib import Path
from rich.console import Console

from wowsql_cli.utils.formatters import format_output, format_query_results

console = Console()


@click.group()
def db_group():
    """Database operation commands."""
    pass


@db_group.group('tables')
def tables_group():
    """Table management commands."""
    pass


@tables_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_tables(ctx, project, format):
    """List all tables."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        tables = api.list_tables(project_slug)
        
        output_format = format or ctx.obj['output']
        format_output(tables, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@tables_group.command('describe')
@click.argument('table_name')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def describe_table(ctx, table_name, project, format):
    """Describe table structure."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        table_info = api.describe_table(project_slug, table_name)
        
        output_format = format or ctx.obj['output']
        format_output(table_info, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('query')
@click.argument('sql', required=False)
@click.option('--file', type=click.Path(exists=True), help='SQL file to execute')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def query(ctx, sql, file, project, format):
    """Execute SQL query."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get SQL from file or argument
        if file:
            with open(file, 'r') as f:
                sql = f.read()
        elif not sql:
            console.print("[red]Error:[/red] SQL query or --file required")
            raise click.Abort()
        
        result = api.query(project_slug, sql)
        
        output_format = format or ctx.obj['output']
        if output_format == 'table':
            format_query_results(result, console)
        else:
            format_output(result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('insert')
@click.argument('table')
@click.option('--data', help='JSON data')
@click.option('--file', type=click.Path(exists=True), help='JSON file with data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def insert_data(ctx, table, data, file, project):
    """Insert data into table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get data from file or argument
        if file:
            with open(file, 'r') as f:
                data_dict = json.load(f)
        elif data:
            data_dict = json.loads(data)
        else:
            console.print("[red]Error:[/red] --data or --file required")
            raise click.Abort()
        
        result = api.insert_data(project_slug, table, data_dict)
        console.print(f"[green]✓[/green] Data inserted successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('update')
@click.argument('table')
@click.option('--where', required=True, help='WHERE clause')
@click.option('--data', required=True, help='JSON data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def update_data(ctx, table, where, data, project):
    """Update data in table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        data_dict = json.loads(data)
        result = api.update_data(project_slug, table, where, data_dict)
        console.print(f"[green]✓[/green] Data updated successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('delete')
@click.argument('table')
@click.option('--where', required=True, help='WHERE clause')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_data(ctx, table, where, project, confirm):
    """Delete data from table."""
    try:
        if not confirm:
            if not click.confirm(f"Delete rows from '{table}' where {where}?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        result = api.delete_data(project_slug, table, where)
        console.print(f"[green]✓[/green] Data deleted successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('export')
@click.argument('table')
@click.option('--output', type=click.Path(), required=True, help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def export_data(ctx, table, output, format, project):
    """Export table data."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Query all data
        result = api.query(project_slug, f"SELECT * FROM `{table}`")
        data = result.get('data', [])
        
        # Write to file
        output_path = Path(output)
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            import csv
            if data:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        console.print(f"[green]✓[/green] Exported {len(data)} rows to {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('import')
@click.argument('table')
@click.option('--file', type=click.Path(exists=True), required=True, help='Input file path')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def import_data(ctx, table, file, project):
    """Import data into table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Read data from file
        file_path = Path(file)
        with open(file_path, 'r') as f:
            if file_path.suffix == '.json':
                data_list = json.load(f)
            else:
                # Assume CSV
                import csv
                reader = csv.DictReader(f)
                data_list = list(reader)
        
        # Insert each row
        count = 0
        for row in data_list:
            api.insert_data(project_slug, table, row)
            count += 1
        
        console.print(f"[green]✓[/green] Imported {count} rows into '{table}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('dump')
@click.option('--output', type=click.Path(), help='Output file path (default: dump.sql)')
@click.option('--schema-only', is_flag=True, help='Export schema only (no data)')
@click.option('--data-only', is_flag=True, help='Export data only (no schema)')
@click.option('--tables', help='Comma-separated list of tables to export')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def dump_database(ctx, output, schema_only, data_only, tables, project):
    """Export entire database to SQL file."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        output_path = Path(output) if output else Path('dump.sql')
        
        console.print(f"[cyan]Exporting database...[/cyan]")
        dump_data = api.dump_database(
            project_slug,
            schema_only=schema_only,
            data_only=data_only,
            tables=tables.split(',') if tables else None
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dump_data.get('sql', ''))
        
        console.print(f"[green]✓[/green] Database exported to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('restore')
@click.option('--file', type=click.Path(exists=True), required=True, help='SQL file to restore')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def restore_database(ctx, file, project, confirm):
    """Restore database from SQL file."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if not confirm:
            if not click.confirm(f"Restore database from '{file}'? This will overwrite existing data."):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        file_path = Path(file)
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        console.print(f"[cyan]Restoring database...[/cyan]")
        result = api.restore_database(project_slug, sql_content)
        
        console.print(f"[green]✓[/green] Database restored successfully")
        if result.get('tables_created'):
            console.print(f"  Tables created: {result.get('tables_created')}")
        if result.get('rows_inserted'):
            console.print(f"  Rows inserted: {result.get('rows_inserted')}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('seed')
@click.option('--file', type=click.Path(exists=True), help='SQL or JSON file with seed data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def seed_database(ctx, file, project):
    """Seed database with initial data."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if file:
            file_path = Path(file)
            if file_path.suffix == '.sql':
                # SQL seed file
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                result = api.query(project_slug, sql_content)
                console.print(f"[green]✓[/green] Database seeded from SQL file")
            else:
                # JSON seed file
                with open(file_path, 'r') as f:
                    seed_data = json.load(f)
                
                count = 0
                for table, rows in seed_data.items():
                    for row in rows:
                        api.insert_data(project_slug, table, row)
                        count += 1
                
                console.print(f"[green]✓[/green] Seeded {count} rows from JSON file")
        else:
            # Look for seed.sql in current directory
            seed_file = Path('seed.sql')
            if seed_file.exists():
                with open(seed_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                result = api.query(project_slug, sql_content)
                console.print(f"[green]✓[/green] Database seeded from seed.sql")
            else:
                console.print("[yellow]No seed file found. Use --file to specify a seed file.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('diff')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def diff_schema(ctx, project, format):
    """Compare local and remote database schemas."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get remote schema
        remote_schema = api.get_schema(project_slug)
        
        # Get local schema from migrations
        migrations_dir = Path('migrations')
        local_schema = {}
        if migrations_dir.exists():
            # In a real implementation, we'd parse migrations to build schema
            console.print("[yellow]Local schema parsing from migrations not yet fully implemented[/yellow]")
        
        # Compare schemas
        diff_result = api.compare_schemas(project_slug, local_schema, remote_schema)
        
        output_format = format or ctx.obj['output']
        if output_format == 'table':
            _display_schema_diff(diff_result)
        else:
            format_output(diff_result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def _display_schema_diff(diff_result: dict):
    """Display schema differences in a table."""
    from rich.table import Table
    
    table = Table(title="Schema Differences")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="gray")
    
    differences = diff_result.get('differences', [])
    for diff in differences:
        table.add_row(
            diff.get('type', ''),
            diff.get('name', ''),
            diff.get('status', ''),
            diff.get('details', '')
        )
    
    console.print(table)
    
    if not differences:
        console.print("\n[green]✓[/green] No schema differences found")


@db_group.group('schema')
def schema_group():
    """Schema management commands."""
    pass


@schema_group.command('dump')
@click.option('--output', type=click.Path(), help='Output file path (default: schema.sql)')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def dump_schema(ctx, output, project):
    """Export database schema only (no data)."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        output_path = Path(output) if output else Path('schema.sql')
        
        console.print(f"[cyan]Exporting schema...[/cyan]")
        dump_data = api.dump_database(project_slug, schema_only=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dump_data.get('sql', ''))
        
        console.print(f"[green]✓[/green] Schema exported to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@schema_group.command('diff')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def schema_diff(ctx, project, format):
    """Show schema differences."""
    ctx.forward(diff_schema)


@db_group.command('connect')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def connect_database(ctx, project):
    """Connect to database interactively."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get database connection info
        connection_info = api.get_database_connection(project_slug)
        
        console.print(f"[cyan]Database Connection Info:[/cyan]")
        console.print(f"  Host: {connection_info.get('host')}")
        console.print(f"  Port: {connection_info.get('port')}")
        console.print(f"  Database: {connection_info.get('database')}")
        console.print(f"  User: {connection_info.get('user')}")
        console.print(f"\n[yellow]Note:[/yellow] Direct MySQL connection not yet implemented.")
        console.print(f"  Use 'wowsql db query' to execute SQL queries.")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('explain')
@click.argument('sql')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def explain_query(ctx, sql, project, format):
    """Explain query execution plan."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        explain_result = api.explain_query(project_slug, sql)
        output_format = format or ctx.obj['output']
        format_output(explain_result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('analyze')
@click.argument('table')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def analyze_table(ctx, table, project):
    """Analyze table and update statistics."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        api.analyze_table(project_slug, table)
        console.print(f"[green]✓[/green] Table '{table}' analyzed")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('optimize')
@click.argument('table')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def optimize_table(ctx, table, project):
    """Optimize table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        api.optimize_table(project_slug, table)
        console.print(f"[green]✓[/green] Table '{table}' optimized")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

