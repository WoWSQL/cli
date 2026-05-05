"""Backup and restore commands."""

import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def backup_group():
    """Backup and restore commands."""
    pass


# ─── CREATE ──────────────────────────────────────────────────────────────────

@backup_group.command('create')
@click.option('--name', help='Backup name (optional)')
@click.option('--output', '-o', type=click.Path(), help='Output path (default: ./<project>_<timestamp>.sql)')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def create_backup(ctx, name, output, project, fmt):
    """
    Create a full database backup and save it to your local device.

    \b
    Examples:
      wowsql backup create
      wowsql backup create --name before-migration --output ./backups/v1.sql
      wowsql backup create --project my-project --output ~/backups/
    """
    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Generating backup...", total=None)
        backup = api.create_backup(project_slug, name=name)

    sql_content = backup.get('sql', '')
    if not sql_content:
        console.print("[yellow]Warning:[/yellow] Server returned an empty backup.")
        return

    # Resolve output path
    backup_id   = backup.get('id', f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_name = backup.get('name', backup_id)
    output_path = Path(output) if output else Path(f"{project_slug}_{backup_id}.sql")

    if output_path.is_dir():
        output_path = output_path / f"{project_slug}_{backup_id}.sql"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql_content, encoding='utf-8')

    console.print(f"[green]Backup saved successfully[/green]")
    console.print(f"  [bold]File:[/bold]   {output_path.absolute()}")
    console.print(f"  [bold]ID:[/bold]     {backup_id}")
    console.print(f"  [bold]Name:[/bold]   {backup_name}")
    console.print(f"  [bold]Tables:[/bold] {len(backup.get('tables_exported', []))}")
    console.print(f"  [bold]Size:[/bold]   {backup.get('size', 'N/A')}")
    console.print(f"  [bold]Created:[/bold] {backup.get('created_at', '')}")
    console.print()
    console.print(f"[dim]To restore later:  wowsql backup restore-file {output_path}[/dim]")


# ─── RESTORE FROM LOCAL FILE ─────────────────────────────────────────────────

@backup_group.command('restore-file')
@click.argument('file', type=click.Path(exists=True, dir_okay=False))
@click.option('--project', help='Project slug (overrides default)')
@click.option('--skip-errors', is_flag=True, help='Continue on statement errors instead of aborting')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def restore_from_file(ctx, file, project, skip_errors, yes):
    """
    Restore database from a local .sql backup file.

    Reads the file from your device and uploads the SQL to be executed
    against your remote project database.

    \b
    Examples:
      wowsql backup restore-file ./myproject_backup_20240501.sql
      wowsql backup restore-file ./backup.sql --skip-errors --yes
    """
    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    sql_path = Path(file)
    file_size_kb = sql_path.stat().st_size / 1024

    console.print(f"[yellow]Warning:[/yellow] This will overwrite your database in project [bold]{project_slug}[/bold].")
    console.print(f"  File:  {sql_path.absolute()}")
    console.print(f"  Size:  {file_size_kb:.1f} KB")

    if not yes:
        if not click.confirm("Are you sure you want to restore? This cannot be undone."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    sql_content = sql_path.read_text(encoding='utf-8')

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Restoring database...", total=None)
        result = api.restore_from_file(project_slug, sql_content, skip_errors=skip_errors)

    if result.get('success'):
        console.print(f"[green]Restore completed successfully[/green]")
        console.print(f"  [bold]Tables created:[/bold]      {result.get('tables_created', 0)}")
        console.print(f"  [bold]Rows inserted:[/bold]       {result.get('rows_inserted', 0)}")
        console.print(f"  [bold]Statements run:[/bold]      {result.get('statements_executed', 0)}")
        errs = result.get('errors', [])
        if errs:
            console.print(f"  [yellow]Errors skipped:[/yellow]      {len(errs)}")
            for err in errs[:5]:
                console.print(f"    [dim]- {err.get('error', '')}[/dim]")
    else:
        console.print(f"[red]Restore failed.[/red]")
        for err in result.get('errors', []):
            console.print(f"  [red]•[/red] {err.get('error', err)}")
        raise click.Abort()


# ─── LIST ─────────────────────────────────────────────────────────────────────

@backup_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def list_backups(ctx, project, fmt):
    """
    List backups recorded in the remote project database.

    Backup records are created automatically by 'wowsql backup create'.
    The actual SQL files are stored on your local device.
    """
    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    try:
        backups = api.list_backups(project_slug)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

    if fmt != 'table':
        format_output(backups, fmt, console)
        return

    if not backups:
        console.print("[yellow]No backup records found.[/yellow]")
        console.print("  Run [cyan]wowsql backup create[/cyan] to create your first backup.")
        return

    table = Table(title=f"Backups for {project_slug}")
    table.add_column("ID",      style="cyan")
    table.add_column("Name",    style="white")
    table.add_column("Created", style="dim")
    table.add_column("Size",    style="yellow")
    table.add_column("Tables",  style="magenta", justify="right")

    for b in backups:
        table.add_row(
            str(b.get('id', '')),
            b.get('name', 'N/A'),
            b.get('created_at', ''),
            b.get('size', 'N/A'),
            str(len(b.get('tables_exported', []))),
        )
    console.print(table)
    console.print(f"[dim]Restore a backup with: wowsql backup restore-file <local-file.sql>[/dim]")


# ─── RESTORE (by ID — legacy stub, redirects to restore-file) ────────────────

@backup_group.command('restore')
@click.argument('file_or_id')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--skip-errors', is_flag=True, help='Continue on statement errors instead of aborting')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def restore_backup(ctx, file_or_id, project, skip_errors, yes):
    """
    Restore database from a local .sql file (or legacy backup ID).

    \b
    Examples:
      wowsql backup restore ./backup.sql
      wowsql backup restore ./backup.sql --yes
    """
    # If argument looks like a file path, delegate to restore-file
    path = Path(file_or_id)
    if path.exists() and path.is_file():
        ctx.invoke(restore_from_file, file=file_or_id, project=project,
                   skip_errors=skip_errors, yes=yes)
    else:
        console.print(f"[red]Error:[/red] '{file_or_id}' is not a valid file path.")
        console.print()
        console.print("Server-side backup restore by ID is not supported.")
        console.print("To restore, first create a backup locally:")
        console.print(f"  [cyan]wowsql backup create --output ./backup.sql[/cyan]")
        console.print("Then restore it:")
        console.print(f"  [cyan]wowsql backup restore-file ./backup.sql[/cyan]")
        raise click.Abort()
