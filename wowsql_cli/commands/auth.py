"""Authentication commands."""

import click
from rich.console import Console
from rich.table import Table

from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def auth_group():
    """Authentication commands."""
    pass


@auth_group.command('login')
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
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@auth_group.command('logout')
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


@auth_group.command('status')
@click.option('--profile', help='Profile name')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def status(ctx, profile, format):
    """Show authentication status."""
    try:
        auth_manager = ctx.obj['auth']
        status_data = auth_manager.get_status(profile=profile)
        
        output_format = format or ctx.obj['output']
        format_output(status_data, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@auth_group.command('switch-profile')
@click.argument('profile_name')
@click.pass_context
def switch_profile(ctx, profile_name):
    """Switch to a different profile."""
    try:
        config = ctx.obj['config']
        config.set_current_profile(profile_name)
        console.print(f"[green]✓[/green] Switched to profile: {profile_name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

