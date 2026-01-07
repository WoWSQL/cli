"""Stored procedures management commands."""

import click
from rich.console import Console
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def procedures_group():
    """Stored procedures management commands."""
    pass


@procedures_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_procedures(ctx, project, format):
    """List all stored procedures."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        procedures = api.list_procedures(project_slug)
        output_format = format or ctx.obj['output']
        format_output(procedures, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@procedures_group.command('create')
@click.argument('procedure_name')
@click.argument('sql', required=False)
@click.option('--file', type=click.Path(exists=True), help='SQL file with procedure definition')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def create_procedure(ctx, procedure_name, sql, file, project):
    """Create a stored procedure."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if file:
            with open(file, 'r') as f:
                procedure_sql = f.read()
        elif sql:
            procedure_sql = sql
        else:
            console.print("[red]Error:[/red] SQL definition or --file required")
            raise click.Abort()
        
        api.create_procedure(project_slug, procedure_name, procedure_sql)
        console.print(f"[green]✓[/green] Procedure '{procedure_name}' created")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@procedures_group.command('execute')
@click.argument('procedure_name')
@click.option('--params', help='JSON parameters for procedure')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def execute_procedure(ctx, procedure_name, params, project, format):
    """Execute a stored procedure."""
    try:
        import json
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        params_dict = json.loads(params) if params else {}
        result = api.execute_procedure(project_slug, procedure_name, params_dict)
        
        output_format = format or ctx.obj['output']
        format_output(result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

