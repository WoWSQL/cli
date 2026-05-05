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
            console.print("  • PostgreSQL:  localhost:5432  (user: postgres / password: postgres / db: wowsql_local)")
            console.print("  • pgAdmin:     http://localhost:5050  (admin@wowsql.local / admin)")
            console.print("  • Redis:       localhost:6379")
            console.print("  • MinIO:       http://localhost:9001  (minioadmin / minioadmin)")
            console.print()
            console.print("  Connect with psql:")
            console.print("    psql -h localhost -p 5432 -U postgres -d wowsql_local")
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
    """Create local development setup files (PostgreSQL stack)."""
    local_dir.mkdir(parents=True, exist_ok=True)

    compose_content = """\
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: wowsql-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: wowsql_local
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: wowsql-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@wowsql.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

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
  postgres_data:
  minio_data:
"""

    with open(local_dir / 'docker-compose.yml', 'w') as f:
        f.write(compose_content)

    init_sql = """\
-- WowSQL local development database initialization
-- PostgreSQL 16

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Example: create a test table
-- CREATE TABLE IF NOT EXISTS example (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT);
"""

    with open(local_dir / 'init.sql', 'w') as f:
        f.write(init_sql)

    console.print("[green]✓[/green] Created local development setup (PostgreSQL)")
    console.print("  docker-compose.yml and init.sql created in:", str(local_dir))

