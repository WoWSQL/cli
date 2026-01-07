"""Backup and restore commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def backup_group():
    """Backup and restore commands."""
    pass


@backup_group.command('create')
@click.option('--name', help='Backup name (optional)')
@click.option('--output', type=click.Path(), help='Output file path (default: backup_YYYYMMDD_HHMMSS.sql)')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def create_backup(ctx, name, output, project, format):
    """Create a database backup and save it locally."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        console.print(f"[cyan]Creating backup...[/cyan]")
        backup = api.create_backup(project_slug, name=name)
        
        # Save SQL content to local file
        backup_id = backup.get('id', 'backup')
        if not output:
            # Generate default filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = Path(f"{backup_id}_{timestamp}.sql")
        else:
            output = Path(output)
        
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Write SQL content to file
        sql_content = backup.get('sql', '')
        if sql_content:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            console.print(f"[green]✓[/green] Backup created and saved successfully")
            console.print(f"  File: {output.absolute()}")
            console.print(f"  ID: {backup.get('id')}")
            console.print(f"  Name: {backup.get('name', 'N/A')}")
            console.print(f"  Created: {backup.get('created_at')}")
            console.print(f"  Size: {backup.get('size', 'N/A')}")
            console.print(f"  Tables: {len(backup.get('tables_exported', []))}")
        else:
            console.print(f"[yellow]Warning:[/yellow] Backup created but SQL content is empty")
            console.print(f"  ID: {backup.get('id')}")
            console.print(f"  Name: {backup.get('name', 'N/A')}")
        
        # If format is not table, also output metadata
        output_format = format or ctx.obj['output']
        if output_format != 'table':
            format_output(backup, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@backup_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_backups(ctx, project, format):
    """List all backups for a project."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        backups = api.list_backups(project_slug)
        
        output_format = format or ctx.obj['output']
        if output_format == 'table':
            if backups:
                table = Table(title="Backups")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="white")
                table.add_column("Created", style="gray")
                table.add_column("Size", style="yellow")
                
                for backup in backups:
                    table.add_row(
                        str(backup.get('id', '')),
                        backup.get('name', 'N/A'),
                        backup.get('created_at', ''),
                        backup.get('size', 'N/A')
                    )
                console.print(table)
            else:
                console.print("[yellow]No backups found[/yellow]")
        else:
            format_output(backups, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@backup_group.command('restore')
@click.argument('backup_id')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def restore_backup(ctx, backup_id, project, confirm):
    """Restore database from backup."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if not confirm:
            if not click.confirm(f"Restore from backup {backup_id}? This will overwrite existing data."):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        console.print(f"[cyan]Restoring from backup...[/cyan]")
        result = api.restore_backup(project_slug, backup_id)
        
        console.print(f"[green]✓[/green] Backup restored successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@backup_group.command('download')
@click.argument('backup_id')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def download_backup(ctx, backup_id, output, project):
    """Download backup file."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        output_path = Path(output) if output else Path(f'backup_{backup_id}.sql')
        
        console.print(f"[cyan]Downloading backup...[/cyan]")
        api.download_backup(project_slug, backup_id, output_path)
        
        console.print(f"[green]✓[/green] Backup downloaded to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

