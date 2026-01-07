"""Configuration management commands."""

import click
from rich.console import Console
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def config_group():
    """Configuration management commands."""
    pass


@config_group.command('get')
@click.argument('key')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def get_config(ctx, key, project):
    """Get a configuration value."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        value = api.get_config(project_slug, key)
        console.print(value)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@config_group.command('set')
@click.argument('key')
@click.argument('value')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def set_config(ctx, key, value, project):
    """Set a configuration value."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        api.set_config(project_slug, key, value)
        console.print(f"[green]✓[/green] Configuration '{key}' set to '{value}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@config_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_config(ctx, project, format):
    """List all configuration values."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        configs = api.list_config(project_slug)
        
        output_format = format or ctx.obj['output']
        format_output(configs, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

