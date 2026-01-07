"""Storage management commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, FileSizeColumn, TransferSpeedColumn

from wowsql_cli.utils.formatters import format_output

console = Console()


@click.group()
def storage_group():
    """Storage management commands."""
    pass


@storage_group.command('list')
@click.option('--prefix', help='Path prefix to filter')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_storage(ctx, prefix, project, format):
    """List storage files."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        files = api.list_storage(project_slug, prefix=prefix)
        
        output_format = format or ctx.obj['output']
        format_output(files, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@storage_group.command('upload')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--path', help='Remote path (default: filename)')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def upload_file(ctx, file_path, path, project):
    """Upload file to storage."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        local_path = Path(file_path)
        remote_path = path or local_path.name
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            FileSizeColumn(),
            TransferSpeedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Uploading {local_path.name}...", total=local_path.stat().st_size)
            result = api.upload_file(project_slug, local_path, remote_path)
            progress.update(task, completed=local_path.stat().st_size)
        
        console.print(f"[green]✓[/green] File uploaded to: {remote_path}")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@storage_group.command('download')
@click.argument('remote_path')
@click.option('--output', type=click.Path(), help='Local output path')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def download_file(ctx, remote_path, output, project):
    """Download file from storage."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        local_path = Path(output) if output else Path(remote_path.split('/')[-1])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            FileSizeColumn(),
            TransferSpeedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Downloading {remote_path}...", total=None)
            api.download_file(project_slug, remote_path, local_path)
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] File downloaded to: {local_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@storage_group.command('delete')
@click.argument('remote_path')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_file(ctx, remote_path, project, confirm):
    """Delete file from storage."""
    try:
        if not confirm:
            if not click.confirm(f"Delete file '{remote_path}'?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        api.delete_file(project_slug, remote_path)
        console.print(f"[green]✓[/green] File deleted: {remote_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@storage_group.command('quota')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def storage_quota(ctx, project, format):
    """Get storage quota information."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # This would need a quota endpoint in the API
        console.print("[yellow]Note:[/yellow] Storage quota endpoint not yet implemented")
        # quota = api.get_storage_quota(project_slug)
        # format_output(quota, format or ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

