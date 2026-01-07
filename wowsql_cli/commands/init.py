"""Project initialization commands."""

import click
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


@click.command()
@click.option('--project', help='Project slug to initialize (optional)')
@click.option('--template', type=click.Choice(['basic', 'api', 'full']), default='basic',
              help='Project template to use')
@click.option('--force', is_flag=True, help='Overwrite existing files')
@click.pass_context
def init(ctx, project, template, force):
    """Initialize a new WoWSQL project in the current directory."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        
        project_dir = Path.cwd()
        project_config_file = project_dir / '.wowsql' / 'config.yaml'
        
        # Check if already initialized
        if project_config_file.exists() and not force:
            if not Confirm.ask("Project already initialized. Overwrite?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Get or create project
        if project:
            try:
                project_info = api.get_project(project)
                project_slug = project
            except Exception as e:
                console.print(f"[red]Error:[/red] Project not found: {e}")
                raise click.Abort()
        else:
            # List projects or create new
            projects = api.get_projects()
            if projects:
                console.print("\n[bold]Available projects:[/bold]")
                for i, p in enumerate(projects, 1):
                    console.print(f"  {i}. {p.get('name', 'Unknown')} ({p.get('slug', 'unknown')})")
                console.print(f"  {len(projects) + 1}. Create new project")
                
                choice = Prompt.ask("\nSelect project", default="1")
                choice_num = int(choice)
                
                if choice_num <= len(projects):
                    project_slug = projects[choice_num - 1].get('slug')
                    project_info = api.get_project(project_slug)
                else:
                    # Create new project
                    project_name = Prompt.ask("Project name")
                    project_info = api.create_project(project_name)
                    project_slug = project_info.get('slug')
                    console.print(f"[green]✓[/green] Created project: {project_name}")
            else:
                # Create new project
                project_name = Prompt.ask("Project name")
                project_info = api.create_project(project_name)
                project_slug = project_info.get('slug')
                console.print(f"[green]✓[/green] Created project: {project_name}")
        
        # Create .wowsql directory
        wowsql_dir = project_dir / '.wowsql'
        wowsql_dir.mkdir(exist_ok=True)
        
        # Save project config
        project_config = {
            'project_slug': project_slug,
            'project_name': project_info.get('name', ''),
            'api_url': config.get_api_url(),
            'template': template
        }
        
        with open(project_config_file, 'w') as f:
            yaml.dump(project_config, f, default_flow_style=False)
        
        # Create migrations directory
        migrations_dir = project_dir / 'migrations'
        migrations_dir.mkdir(exist_ok=True)
        
        # Create .gitignore if doesn't exist
        gitignore_file = project_dir / '.gitignore'
        gitignore_content = ""
        if gitignore_file.exists():
            gitignore_content = gitignore_file.read_text()
        
        if '.wowsql' not in gitignore_content:
            gitignore_content += "\n# WoWSQL\n.wowsql/\n"
            gitignore_file.write_text(gitignore_content)
        
        # Create template files
        if template == 'api':
            _create_api_template(project_dir, project_slug)
        elif template == 'full':
            _create_full_template(project_dir, project_slug)
        else:
            _create_basic_template(project_dir, project_slug)
        
        console.print(f"\n[green]✓[/green] Project initialized!")
        console.print(f"  Project: {project_info.get('name', project_slug)}")
        console.print(f"  Directory: {project_dir}")
        console.print(f"\nNext steps:")
        console.print(f"  1. Create a migration: wowsql migration new <name>")
        console.print(f"  2. Apply migrations: wowsql migration up")
        console.print(f"  3. Query database: wowsql db query \"SELECT 1\"")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def _create_basic_template(project_dir: Path, project_slug: str):
    """Create basic project template."""
    # Create README
    readme_file = project_dir / 'README.md'
    if not readme_file.exists():
        readme_content = f"""# {project_slug}

WoWSQL Project

## Getting Started

1. Create migrations: `wowsql migration new <name>`
2. Apply migrations: `wowsql migration up`
3. Query database: `wowsql db query "SELECT 1"`
"""
        readme_file.write_text(readme_content)


def _create_api_template(project_dir: Path, project_slug: str):
    """Create API project template."""
    _create_basic_template(project_dir, project_slug)
    
    # Create example API structure
    api_dir = project_dir / 'api'
    api_dir.mkdir(exist_ok=True)
    
    example_file = api_dir / 'example.py'
    if not example_file.exists():
        example_content = """# Example API endpoint
# This is a template for creating API endpoints

def handler(request):
    # Your API logic here
    return {"message": "Hello from WoWSQL API"}
"""
        example_file.write_text(example_content)


def _create_full_template(project_dir: Path, project_slug: str):
    """Create full project template."""
    _create_api_template(project_dir, project_slug)
    
    # Create additional directories
    (project_dir / 'scripts').mkdir(exist_ok=True)
    (project_dir / 'docs').mkdir(exist_ok=True)
    
    # Create seed file
    seed_file = project_dir / 'seed.sql'
    if not seed_file.exists():
        seed_content = """-- Seed data for development
-- Run with: wowsql db seed

-- Example seed data
-- INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');
"""
        seed_file.write_text(seed_content)

