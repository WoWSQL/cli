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

