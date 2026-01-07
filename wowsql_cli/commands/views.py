"""Database views management commands."""

import click
from rich.console import Console
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def views_group():
    """Database views management commands."""
    pass


@views_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_views(ctx, project, format):
    """List all database views."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        views = api.list_views(project_slug)
        output_format = format or ctx.obj['output']
        format_output(views, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@views_group.command('create')
@click.argument('view_name')
@click.argument('sql', required=False)
@click.option('--file', type=click.Path(exists=True), help='SQL file with view definition')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def create_view(ctx, view_name, sql, file, project):
    """Create a database view."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if file:
            with open(file, 'r') as f:
                view_sql = f.read()
        elif sql:
            view_sql = sql
        else:
            console.print("[red]Error:[/red] SQL definition or --file required")
            raise click.Abort()
        
        api.create_view(project_slug, view_name, view_sql)
        console.print(f"[green]✓[/green] View '{view_name}' created")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@views_group.command('describe')
@click.argument('view_name')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def describe_view(ctx, view_name, project, format):
    """Describe view structure."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        view_info = api.describe_view(project_slug, view_name)
        output_format = format or ctx.obj['output']
        format_output(view_info, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

