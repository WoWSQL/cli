"""Validation commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def validate(ctx, project):
    """Validate project configuration and schema."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        console.print("[cyan]Validating project...[/cyan]\n")
        
        # Validate project access
        try:
            project_info = api.get_project(project_slug)
            console.print(f"[green]✓[/green] Project access: OK")
        except Exception as e:
            console.print(f"[red]✗[/red] Project access: FAILED - {e}")
            raise click.Abort()
        
        # Validate database connection
        try:
            api.query(project_slug, "SELECT 1")
            console.print(f"[green]✓[/green] Database connection: OK")
        except Exception as e:
            console.print(f"[red]✗[/red] Database connection: FAILED - {e}")
        
        # Validate schema
        try:
            schema = api.get_schema(project_slug)
            tables = schema.get('tables', [])
            console.print(f"[green]✓[/green] Schema validation: OK ({len(tables)} tables)")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Schema validation: WARNING - {e}")
        
        # Validate migrations
        try:
            migrations_dir = Path('migrations')
            if migrations_dir.exists():
                migration_files = list(migrations_dir.glob('*.sql'))
                console.print(f"[green]✓[/green] Migrations: OK ({len(migration_files)} files)")
            else:
                console.print(f"[yellow]⚠[/yellow] Migrations: No migrations directory found")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Migrations: WARNING - {e}")
        
        console.print(f"\n[green]✓[/green] Validation complete")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

