"""Migration management commands."""

import click
from pathlib import Path
from datetime import datetime
from rich.console import Console

from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def migration_group():
    """Migration management commands."""
    pass


@migration_group.command('new')
@click.argument('name')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def new_migration(ctx, name, project):
    """
    Create a new migration file pair.

    Creates two files:
      migrations/<timestamp>_<name>.sql       — the UP migration (apply)
      migrations/<timestamp>_<name>.down.sql  — the DOWN migration (rollback)
    """
    try:
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()

        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()

        migrations_dir = Path('migrations')
        migrations_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_name = name.lower().replace(' ', '_').replace('-', '_')

        up_file   = migrations_dir / f"{timestamp}_{safe_name}.sql"
        down_file = migrations_dir / f"{timestamp}_{safe_name}.down.sql"

        with open(up_file, 'w') as f:
            f.write(f"-- Migration: {name}\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Direction: UP (apply)\n\n")
            f.write("-- Add your UP SQL here\n")
            f.write("-- Example: CREATE TABLE ...\n")

        with open(down_file, 'w') as f:
            f.write(f"-- Migration: {name}\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Direction: DOWN (rollback / undo)\n\n")
            f.write("-- Add your DOWN SQL here\n")
            f.write("-- Example: DROP TABLE IF EXISTS ...\n")

        console.print(f"[green]✓[/green] Created migration files:")
        console.print(f"  UP:   {up_file}")
        console.print(f"  DOWN: {down_file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@migration_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_migrations(ctx, project, format):
    """List all migrations."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        history = api.get_migration_history(project_slug)
        
        output_format = format or ctx.obj['output']
        format_output(history, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@migration_group.command('status')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def migration_status(ctx, project):
    """Show migration status."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get applied migrations
        history = api.get_migration_history(project_slug)
        applied = {m['migration_name'] for m in history if not m.get('rolled_back_at')}
        
        # Get local migrations
        migrations_dir = Path('migrations')
        if migrations_dir.exists():
            local_migrations = sorted([
                f.stem for f in migrations_dir.glob('*.sql')
                if not f.name.endswith('.down.sql')
            ])
        else:
            local_migrations = []
        
        console.print(f"\n[bold]Migration Status[/bold]")
        console.print(f"Applied: {len(applied)}")
        console.print(f"Local: {len(local_migrations)}")
        
        # Show pending migrations
        pending = [m for m in local_migrations if m not in applied]
        if pending:
            console.print(f"\n[yellow]Pending migrations:[/yellow]")
            for m in pending:
                console.print(f"  • {m}")
        else:
            console.print("\n[green]✓[/green] All migrations applied")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@migration_group.command('up')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--dry-run', is_flag=True, help='Show what would be applied without executing')
@click.pass_context
def apply_migrations(ctx, project, dry_run):
    """Apply pending migrations."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get applied migrations
        history = api.get_migration_history(project_slug)
        applied = {m['migration_name'] for m in history if not m.get('rolled_back_at')}
        
        # Get local migrations
        migrations_dir = Path('migrations')
        if not migrations_dir.exists():
            console.print("[yellow]No migrations directory found[/yellow]")
            return
        
        local_files = sorted([
            f for f in migrations_dir.glob('*.sql')
            if not f.name.endswith('.down.sql')
        ])
        pending = [f for f in local_files if f.stem not in applied]
        
        if not pending:
            console.print("[green]✓[/green] No pending migrations")
            return
        
        if dry_run:
            console.print(f"[yellow]Would apply {len(pending)} migrations:[/yellow]")
            for f in pending:
                console.print(f"  • {f.name}")
            return
        
        # Apply each migration
        for migration_file in pending:
            console.print(f"Applying {migration_file.name}...")
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            result = api.apply_migration(project_slug, migration_file.stem, sql)
            console.print(f"[green]✓[/green] Applied: {migration_file.name}")
        
        console.print(f"\n[green]✓[/green] Applied {len(pending)} migration(s)")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@migration_group.command('down')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--count', type=int, default=1, help='Number of migrations to rollback')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def rollback_migrations(ctx, project, count, yes):
    """
    Rollback the last N applied migrations.

    Looks for a matching <name>.down.sql file in the migrations/ directory
    and executes it before marking the migration as rolled back.
    If no .down.sql file is found you will be warned and asked to confirm.
    """
    try:
        api    = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()

        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()

        history = api.get_migration_history(project_slug)
        applied = [m for m in history if not m.get('rolled_back_at')]
        applied.sort(key=lambda x: x['applied_at'], reverse=True)

        if not applied:
            console.print("[yellow]No migrations to rollback[/yellow]")
            return

        to_rollback = applied[:count]
        migrations_dir = Path('migrations')

        # Preview what will be rolled back
        console.print(f"[yellow]Will rollback {len(to_rollback)} migration(s):[/yellow]")
        for m in to_rollback:
            mname = m['migration_name']
            down_file = migrations_dir / f"{mname}.down.sql"
            has_down = down_file.exists()
            status_str = f"[green]has .down.sql[/green]" if has_down else "[red]NO .down.sql — schema changes will NOT be undone[/red]"
            console.print(f"  • {mname}  {status_str}")

        if not yes:
            if not click.confirm("Proceed with rollback?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        for migration in to_rollback:
            mname = migration['migration_name']
            console.print(f"Rolling back [cyan]{mname}[/cyan]...")

            down_file = migrations_dir / f"{mname}.down.sql"
            if down_file.exists():
                down_sql = down_file.read_text(encoding='utf-8')
                result = api.rollback_migration(project_slug, mname, down_sql=down_sql)
            else:
                console.print(f"  [yellow]Warning:[/yellow] No {mname}.down.sql — only marking as rolled back in metadata")
                result = api.rollback_migration(project_slug, mname, down_sql=None)

            console.print(f"  [green]✓[/green] Rolled back: {mname}")

        console.print(f"\n[green]✓[/green] Rolled back {len(to_rollback)} migration(s)")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

