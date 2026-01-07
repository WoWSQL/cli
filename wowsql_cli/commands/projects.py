"""Project management commands."""

import click
from rich.console import Console
from rich.table import Table

from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def projects_group():
    """Project management commands."""
    pass


@projects_group.command('list')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_projects(ctx, format):
    """List all projects."""
    try:
        api = ctx.obj['api']
        projects = api.get_projects()
        
        output_format = format or ctx.obj['output']
        format_output(projects, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('get')
@click.argument('slug')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def get_project(ctx, slug, format):
    """Get project details."""
    try:
        api = ctx.obj['api']
        project = api.get_project(slug)
        
        output_format = format or ctx.obj['output']
        format_output(project, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('create')
@click.argument('name')
@click.option('--password', help='Database password')
@click.option('--description', help='Project description')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def create_project(ctx, name, password, description, format):
    """Create a new project."""
    try:
        api = ctx.obj['api']
        kwargs = {}
        if description:
            kwargs['description'] = description
        
        project = api.create_project(name, db_password=password, **kwargs)
        
        output_format = format or ctx.obj['output']
        format_output(project, output_format, console)
        
        console.print(f"\n[green]✓[/green] Project created successfully!")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('update')
@click.argument('slug')
@click.option('--name', help='New project name')
@click.option('--description', help='New project description')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def update_project(ctx, slug, name, description, format):
    """Update project."""
    try:
        api = ctx.obj['api']
        kwargs = {}
        if name:
            kwargs['name'] = name
        if description:
            kwargs['description'] = description
        
        project = api.update_project(slug, **kwargs)
        
        output_format = format or ctx.obj['output']
        format_output(project, output_format, console)
        
        console.print(f"\n[green]✓[/green] Project updated successfully!")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('delete')
@click.argument('slug')
@click.option('--force', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_project(ctx, slug, force):
    """Delete a project."""
    try:
        if not force:
            if not click.confirm(f"Are you sure you want to delete project '{slug}'? This cannot be undone."):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        api = ctx.obj['api']
        api.delete_project(slug)
        
        console.print(f"[green]✓[/green] Project '{slug}' deleted successfully!")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('set-default')
@click.argument('slug')
@click.pass_context
def set_default_project(ctx, slug):
    """Set default project for current profile."""
    try:
        config = ctx.obj['config']
        config.set_default_project(slug)
        console.print(f"[green]✓[/green] Default project set to: {slug}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@projects_group.command('current')
@click.pass_context
def current_project(ctx):
    """Show current default project."""
    try:
        config = ctx.obj['config']
        project_slug = config.get_default_project()
        if project_slug:
            console.print(f"Current project: [cyan]{project_slug}[/cyan]")
        else:
            console.print("[yellow]No default project set[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

