"""Database triggers management commands."""

import click
from rich.console import Console
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def triggers_group():
    """Database triggers management commands."""
    pass


@triggers_group.command('list')
@click.argument('table', required=False)
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_triggers(ctx, table, project, format):
    """List triggers for a table or all tables."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        triggers = api.list_triggers(project_slug, table=table)
        output_format = format or ctx.obj['output']
        format_output(triggers, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@triggers_group.command('create')
@click.argument('trigger_name')
@click.argument('table')
@click.argument('timing', type=click.Choice(['BEFORE', 'AFTER']))
@click.argument('event', type=click.Choice(['INSERT', 'UPDATE', 'DELETE']))
@click.argument('sql', required=False)
@click.option('--file', type=click.Path(exists=True), help='SQL file with trigger body')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def create_trigger(ctx, trigger_name, table, timing, event, sql, file, project):
    """Create a database trigger."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if file:
            with open(file, 'r') as f:
                trigger_body = f.read()
        elif sql:
            trigger_body = sql
        else:
            console.print("[red]Error:[/red] SQL body or --file required")
            raise click.Abort()
        
        api.create_trigger(project_slug, trigger_name, table, timing, event, trigger_body)
        console.print(f"[green]✓[/green] Trigger '{trigger_name}' created on '{table}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@triggers_group.command('delete')
@click.argument('trigger_name')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_trigger(ctx, trigger_name, project, confirm):
    """Delete a trigger."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if not confirm:
            if not click.confirm(f"Delete trigger '{trigger_name}'?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        api.delete_trigger(project_slug, trigger_name)
        console.print(f"[green]✓[/green] Trigger '{trigger_name}' deleted")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

