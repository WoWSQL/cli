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
@click.option('--follow', '-f', is_flag=True, help='Follow log output (polls every 5 s)')
@click.option('--filter', 'log_filter', help='Filter: comma-separated key:value pairs e.g. service:app,level:error')
@click.option('--limit', type=int, default=50, show_default=True, help='Number of entries to show')
@click.option('--source', type=click.Choice(['all', 'activity', 'statements']), default='all',
              show_default=True, help='Which data source to show')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def view_logs(ctx, project, follow, log_filter, limit, source, fmt):
    """
    View database activity logs for a project.

    Shows live sessions from pg_stat_activity and (if available)
    historical query stats from pg_stat_statements.

    \b
    Examples:
      wowsql logs view
      wowsql logs view --limit 20 --source activity
      wowsql logs view --filter level:error
      wowsql logs view --follow
    """
    import time

    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    def _fetch_and_display():
        response = api.get_logs(project_slug, filter=log_filter, limit=limit, follow=False)
        logs = response.get('logs', [])

        if source != 'all':
            src_key = 'pg_stat_activity' if source == 'activity' else 'pg_stat_statements'
            logs = [l for l in logs if l.get('source') == src_key]

        if fmt != 'table':
            format_output(logs, fmt, console)
            return

        if not logs:
            console.print("[yellow]No log entries found.[/yellow]")
            return

        # Show activity logs
        activity = [l for l in logs if l.get('source') == 'pg_stat_activity']
        statements = [l for l in logs if l.get('source') == 'pg_stat_statements']

        if activity:
            act_table = Table(title="Active Sessions (pg_stat_activity)", show_lines=False)
            act_table.add_column("PID",       style="cyan",  no_wrap=True)
            act_table.add_column("User",      style="white")
            act_table.add_column("State",     style="yellow")
            act_table.add_column("Dur(s)",    style="magenta", justify="right")
            act_table.add_column("Wait",      style="dim")
            act_table.add_column("Query",     style="white",  max_width=60)
            for entry in activity:
                dur = str(entry.get('duration_sec', '')) if entry.get('duration_sec') is not None else ''
                act_table.add_row(
                    str(entry.get('pid', '')),
                    entry.get('username', ''),
                    entry.get('state', ''),
                    dur,
                    entry.get('wait_event') or '',
                    (entry.get('query') or '').replace('\n', ' ')[:80],
                )
            console.print(act_table)

        if statements:
            st_table = Table(title="Top Queries (pg_stat_statements)", show_lines=False)
            st_table.add_column("Calls",    style="cyan",    justify="right")
            st_table.add_column("Total ms", style="yellow",  justify="right")
            st_table.add_column("Mean ms",  style="magenta", justify="right")
            st_table.add_column("Rows",     style="white",   justify="right")
            st_table.add_column("Query",    style="white",   max_width=70)
            for entry in statements:
                st_table.add_row(
                    str(entry.get('calls', '')),
                    str(entry.get('total_ms', '')),
                    str(entry.get('mean_ms', '')),
                    str(entry.get('rows', '')),
                    (entry.get('query') or '').replace('\n', ' ')[:90],
                )
            console.print(st_table)

        sources = response.get('sources', [])
        console.print(f"[dim]Sources: {', '.join(sources) or 'none'}  |  Total: {response.get('total', 0)}[/dim]")

    _fetch_and_display()

    if follow:
        console.print("[dim]Following logs — Ctrl+C to stop[/dim]")
        try:
            while True:
                time.sleep(5)
                console.clear()
                _fetch_and_display()
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped.[/yellow]")


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

