"""Main CLI entry point for WoWSQL."""

import click
from rich.console import Console
from rich.table import Table

from wowsql_cli.config import Config
from wowsql_cli.auth import AuthManager
from wowsql_cli.api import APIClient
from wowsql_cli import __version__

# Import command groups
from wowsql_cli.commands import auth, projects, db, storage, migration, types, local, link, secrets

console = Console()


@click.group()
@click.option('--profile', help='Use specific profile')
@click.option('--output', type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='Output format')
@click.version_option(version=__version__, prog_name='wowsql')
@click.pass_context
def cli(ctx, profile, output):
    """WoWSQL CLI - Manage your backend from the command line."""
    ctx.ensure_object(dict)
    
    # Initialize config
    config = Config(profile=profile)
    ctx.obj['config'] = config
    ctx.obj['output'] = output
    
    # Initialize auth and API client
    auth_manager = AuthManager(config)
    ctx.obj['auth'] = auth_manager
    ctx.obj['api'] = APIClient(config, auth_manager)


# Add command groups
cli.add_command(auth.auth_group, name='auth')
cli.add_command(projects.projects_group, name='projects')
cli.add_command(projects.projects_group, name='project')  # Alias for convenience
cli.add_command(db.db_group, name='db')
cli.add_command(storage.storage_group, name='storage')
cli.add_command(migration.migration_group, name='migration')
cli.add_command(types.types_group, name='gen')
cli.add_command(local.local_group, name='local')
cli.add_command(link.link_group, name='link')
cli.add_command(secrets.secrets_group, name='secrets')

# Add top-level aliases for common commands
@cli.command()
@click.option('--email', help='Email address')
@click.option('--password', help='Password (not recommended, use prompt)')
@click.option('--api-key', help='API key for direct authentication')
@click.option('--profile', help='Profile name')
@click.pass_context
def login(ctx, email, password, api_key, profile):
    """Login to WoWSQL."""
    try:
        auth_manager = ctx.obj['auth']
        auth_manager.login(email=email, password=password, api_key=api_key, profile=profile)
        # Refresh API client headers after login
        ctx.obj['api']._update_headers()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

@cli.command()
@click.option('--profile', help='Profile name')
@click.pass_context
def logout(ctx, profile):
    """Logout from WoWSQL."""
    try:
        auth_manager = ctx.obj['auth']
        auth_manager.logout(profile=profile)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
def version():
    """Show version information."""
    console.print(f"[bold]WoWSQL CLI[/bold] version [cyan]{__version__}[/cyan]")


if __name__ == '__main__':
    cli()

