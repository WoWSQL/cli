"""Database indexes management commands."""

import click
from rich.console import Console
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def indexes_group():
    """Database indexes management commands."""
    pass


@indexes_group.command('list')
@click.argument('table', required=False)
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_indexes(ctx, table, project, format):
    """List indexes for a table or all tables."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        indexes = api.list_indexes(project_slug, table=table)
        output_format = format or ctx.obj['output']
        format_output(indexes, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@indexes_group.command('create')
@click.argument('index_name')
@click.argument('table')
@click.argument('columns')
@click.option('--unique', is_flag=True, help='Create unique index')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def create_index(ctx, index_name, table, columns, unique, project):
    """Create an index on a table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        column_list = [col.strip() for col in columns.split(',')]
        api.create_index(project_slug, table, index_name, column_list, unique=unique)
        console.print(f"[green]✓[/green] Index '{index_name}' created on '{table}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@indexes_group.command('analyze')
@click.argument('table')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def analyze_indexes(ctx, table, project, format):
    """Analyze index usage for a table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        analysis = api.analyze_indexes(project_slug, table)
        output_format = format or ctx.obj['output']
        format_output(analysis, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

