"""Project linking commands."""

import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.group()
def link_group():
    """Project linking commands."""
    pass


@link_group.command()
@click.option('--project', help='Project slug to link')
@click.pass_context
def link(ctx, project):
    """Link current directory to a WoWSQL project."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        
        # Get project slug
        if not project:
            # List projects and let user choose
            projects = api.get_projects()
            if not projects:
                console.print("[yellow]No projects found. Create one first with 'wowsql projects create'[/yellow]")
                raise click.Abort()
            
            console.print("\n[bold]Available projects:[/bold]")
            for i, p in enumerate(projects, 1):
                console.print(f"  {i}. {p.get('name', 'Unknown')} ({p.get('slug', 'unknown')})")
            
            choice = click.prompt("\nSelect project", type=int)
            if choice < 1 or choice > len(projects):
                console.print("[red]Invalid selection[/red]")
                raise click.Abort()
            
            project_slug = projects[choice - 1].get('slug')
        else:
            project_slug = project
        
        # Verify project exists
        try:
            project_info = api.get_project(project_slug)
        except Exception as e:
            console.print(f"[red]Error:[/red] Project not found: {e}")
            raise click.Abort()
        
        # Save project config
        project_dir = Path.cwd()
        project_config = {
            'project_slug': project_slug,
            'project_name': project_info.get('name', ''),
            'api_url': config.get_api_url()
        }
        
        config.save_project_config(project_dir, project_config)
        
        console.print(f"[green]✓[/green] Linked to project: {project_info.get('name', project_slug)}")
        console.print(f"  Project directory: {project_dir}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@link_group.command()
@click.pass_context
def unlink(ctx):
    """Unlink current directory from WoWSQL project."""
    try:
        project_dir = Path.cwd()
        project_config_dir = project_dir / ".wowsql"
        
        if not project_config_dir.exists():
            console.print("[yellow]No project linked in this directory[/yellow]")
            return
        
        if click.confirm("Unlink this directory from WoWSQL project?"):
            import shutil
            shutil.rmtree(project_config_dir)
            console.print("[green]✓[/green] Unlinked from project")
        else:
            console.print("[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

