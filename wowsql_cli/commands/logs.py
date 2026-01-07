"""Logs and monitoring commands."""

import click
from rich.console import Console
from rich.table import Table
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def logs_group():
    """Logs and monitoring commands."""
    pass


@logs_group.command('view')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--filter', help='Filter logs by service/level')
@click.option('--limit', type=int, default=100, help='Number of log entries to show')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def view_logs(ctx, project, follow, filter, limit, format):
    """View project logs."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get logs from API
        logs = api.get_logs(project_slug, filter=filter, limit=limit, follow=follow)
        
        output_format = format or ctx.obj['output']
        format_output(logs, output_format, console)
        
        if follow:
            console.print("[yellow]Following logs... (Press Ctrl+C to stop)[/yellow]")
            # In a real implementation, this would stream logs
            # For now, just show initial logs
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@logs_group.command('status')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def status(ctx, project, format):
    """Show project status and health."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get project status
        status_info = api.get_project_status(project_slug)
        
        output_format = format or ctx.obj['output']
        if output_format == 'table':
            _display_status_table(status_info)
        else:
            format_output(status_info, output_format, console)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def _display_status_table(status_info: dict):
    """Display status in a formatted table."""
    table = Table(title="Project Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    services = status_info.get('services', {})
    for service, info in services.items():
        status_icon = "✓" if info.get('status') == 'healthy' else "✗"
        status_text = info.get('status', 'unknown').upper()
        details = info.get('details', '')
        table.add_row(service, f"{status_icon} {status_text}", details)
    
    console.print(table)
    
    # Show overall health
    overall = status_info.get('overall', 'unknown')
    if overall == 'healthy':
        console.print(f"\n[green]✓ Overall Status: HEALTHY[/green]")
    else:
        console.print(f"\n[yellow]⚠ Overall Status: {overall.upper()}[/yellow]")

