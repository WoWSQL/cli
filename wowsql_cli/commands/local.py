"""Local development environment commands."""

import click
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def local_group():
    """Local development environment commands."""
    pass


@local_group.command('start')
@click.pass_context
def start_local(ctx):
    """Start local development environment."""
    try:
        console.print("[yellow]Starting local development environment...[/yellow]")
        
        # Check if Docker is available
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]Error:[/red] Docker is not installed or not running")
            console.print("Please install Docker: https://docs.docker.com/get-docker/")
            raise click.Abort()
        
        # Get docker-compose file path
        local_dir = Path(__file__).parent.parent / 'local'
        compose_file = local_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            console.print("[yellow]Creating local development setup...[/yellow]")
            _create_local_setup(local_dir)
        
        # Start services
        console.print("[cyan]Starting services...[/cyan]")
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'up', '-d'],
            cwd=local_dir
        )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Local environment started")
            console.print("\nServices:")
            console.print("  • MySQL: localhost:3306")
            console.print("  • Redis: localhost:6379")
            console.print("  • MinIO: localhost:9000")
        else:
            console.print("[red]Error:[/red] Failed to start services")
            raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@local_group.command('stop')
@click.pass_context
def stop_local(ctx):
    """Stop local development environment."""
    try:
        local_dir = Path(__file__).parent.parent / 'local'
        compose_file = local_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            console.print("[yellow]Local environment not set up[/yellow]")
            return
        
        console.print("[cyan]Stopping services...[/cyan]")
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'down'],
            cwd=local_dir
        )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Local environment stopped")
        else:
            console.print("[red]Error:[/red] Failed to stop services")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@local_group.command('status')
@click.pass_context
def local_status(ctx):
    """Check local services status."""
    try:
        local_dir = Path(__file__).parent.parent / 'local'
        compose_file = local_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            console.print("[yellow]Local environment not set up[/yellow]")
            return
        
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'ps'],
            cwd=local_dir,
            capture_output=True,
            text=True
        )
        
        console.print(result.stdout)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@local_group.command('reset')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def reset_local(ctx, confirm):
    """Reset local database."""
    try:
        if not confirm:
            if not click.confirm("This will delete all local data. Continue?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        local_dir = Path(__file__).parent.parent / 'local'
        compose_file = local_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            console.print("[yellow]Local environment not set up[/yellow]")
            return
        
        console.print("[cyan]Resetting local database...[/cyan]")
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'down', '-v'],
            cwd=local_dir
        )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Local database reset")
        else:
            console.print("[red]Error:[/red] Failed to reset database")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@local_group.command('logs')
@click.option('--service', help='Service name to show logs for')
@click.pass_context
def local_logs(ctx, service):
    """View service logs."""
    try:
        local_dir = Path(__file__).parent.parent / 'local'
        compose_file = local_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            console.print("[yellow]Local environment not set up[/yellow]")
            return
        
        cmd = ['docker-compose', '-f', str(compose_file), 'logs']
        if service:
            cmd.append(service)
        
        subprocess.run(cmd, cwd=local_dir)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def _create_local_setup(local_dir: Path):
    """Create local development setup files."""
    local_dir.mkdir(parents=True, exist_ok=True)
    
    # Create docker-compose.yml
    compose_content = """version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: wowsql-mysql
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: wowsql_local
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: wowsql-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: wowsql-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  mysql_data:
  minio_data:
"""
    
    with open(local_dir / 'docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    # Create init.sql
    init_sql = """-- Local development database initialization
CREATE DATABASE IF NOT EXISTS wowsql_local;
USE wowsql_local;
"""
    
    with open(local_dir / 'init.sql', 'w') as f:
        f.write(init_sql)
    
    console.print("[green]✓[/green] Created local development setup")

