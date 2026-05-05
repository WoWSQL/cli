"""Database operation commands."""

import click
import json
from pathlib import Path
from rich.console import Console

from wowsql_cli.utils.formatters import format_output, format_query_results

console = Console()


@click.group()
def db_group():
    """Database operation commands."""
    pass


@db_group.group('tables')
def tables_group():
    """Table management commands."""
    pass


@tables_group.command('list')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_tables(ctx, project, format):
    """List all tables."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        tables = api.list_tables(project_slug)
        
        output_format = format or ctx.obj['output']
        format_output(tables, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@tables_group.command('describe')
@click.argument('table_name')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def describe_table(ctx, table_name, project, format):
    """Describe table structure."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        table_info = api.describe_table(project_slug, table_name)
        
        output_format = format or ctx.obj['output']
        format_output(table_info, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('query')
@click.argument('sql', required=False)
@click.option('--file', type=click.Path(exists=True), help='SQL file to execute')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def query(ctx, sql, file, project, format):
    """Execute SQL query."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get SQL from file or argument
        if file:
            with open(file, 'r') as f:
                sql = f.read()
        elif not sql:
            console.print("[red]Error:[/red] SQL query or --file required")
            raise click.Abort()
        
        result = api.query(project_slug, sql)
        
        output_format = format or ctx.obj['output']
        if output_format == 'table':
            format_query_results(result, console)
        else:
            format_output(result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('insert')
@click.argument('table')
@click.option('--data', help='JSON data')
@click.option('--file', type=click.Path(exists=True), help='JSON file with data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def insert_data(ctx, table, data, file, project):
    """Insert data into table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get data from file or argument
        if file:
            with open(file, 'r') as f:
                data_dict = json.load(f)
        elif data:
            data_dict = json.loads(data)
        else:
            console.print("[red]Error:[/red] --data or --file required")
            raise click.Abort()
        
        result = api.insert_data(project_slug, table, data_dict)
        console.print(f"[green]✓[/green] Data inserted successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('update')
@click.argument('table')
@click.option('--where', required=True, help='WHERE clause')
@click.option('--data', required=True, help='JSON data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def update_data(ctx, table, where, data, project):
    """Update data in table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        data_dict = json.loads(data)
        result = api.update_data(project_slug, table, where, data_dict)
        console.print(f"[green]✓[/green] Data updated successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('delete')
@click.argument('table')
@click.option('--where', required=True, help='WHERE clause')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_data(ctx, table, where, project, confirm):
    """Delete data from table."""
    try:
        if not confirm:
            if not click.confirm(f"Delete rows from '{table}' where {where}?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        result = api.delete_data(project_slug, table, where)
        console.print(f"[green]✓[/green] Data deleted successfully!")
        format_output(result, ctx.obj['output'], console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('export')
@click.argument('table')
@click.option('--output', type=click.Path(), required=True, help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def export_data(ctx, table, output, format, project):
    """Export table data."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Query all data (PostgreSQL double-quote identifiers)
        result = api.query(project_slug, f'SELECT * FROM "{table}"')
        data = result.get('data', [])
        
        # Write to file
        output_path = Path(output)
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            import csv
            if data:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        console.print(f"[green]✓[/green] Exported {len(data)} rows to {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('import')
@click.argument('table')
@click.option('--file', type=click.Path(exists=True), required=True, help='Input file path')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def import_data(ctx, table, file, project):
    """Import data into table."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Read data from file
        file_path = Path(file)
        with open(file_path, 'r') as f:
            if file_path.suffix == '.json':
                data_list = json.load(f)
            else:
                # Assume CSV
                import csv
                reader = csv.DictReader(f)
                data_list = list(reader)
        
        # Insert each row
        count = 0
        for row in data_list:
            api.insert_data(project_slug, table, row)
            count += 1
        
        console.print(f"[green]✓[/green] Imported {count} rows into '{table}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('dump')
@click.option('--output', type=click.Path(), help='Output file path (default: dump.sql)')
@click.option('--schema-only', is_flag=True, help='Export schema only (no data)')
@click.option('--data-only', is_flag=True, help='Export data only (no schema)')
@click.option('--tables', help='Comma-separated list of tables to export')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def dump_database(ctx, output, schema_only, data_only, tables, project):
    """Export entire database to SQL file."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        output_path = Path(output) if output else Path('dump.sql')
        
        console.print(f"[cyan]Exporting database...[/cyan]")
        dump_data = api.dump_database(
            project_slug,
            schema_only=schema_only,
            data_only=data_only,
            tables=tables.split(',') if tables else None
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dump_data.get('sql', ''))
        
        console.print(f"[green]✓[/green] Database exported to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('restore')
@click.option('--file', type=click.Path(exists=True), required=True, help='SQL file to restore')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--confirm', is_flag=True, help='Skip confirmation')
@click.pass_context
def restore_database(ctx, file, project, confirm):
    """Restore database from SQL file."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if not confirm:
            if not click.confirm(f"Restore database from '{file}'? This will overwrite existing data."):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        file_path = Path(file)
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        console.print(f"[cyan]Restoring database...[/cyan]")
        result = api.restore_database(project_slug, sql_content)
        
        console.print(f"[green]✓[/green] Database restored successfully")
        if result.get('tables_created'):
            console.print(f"  Tables created: {result.get('tables_created')}")
        if result.get('rows_inserted'):
            console.print(f"  Rows inserted: {result.get('rows_inserted')}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('seed')
@click.option('--file', type=click.Path(exists=True), help='SQL or JSON file with seed data')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def seed_database(ctx, file, project):
    """Seed database with initial data."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        if file:
            file_path = Path(file)
            if file_path.suffix == '.sql':
                # SQL seed file
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                result = api.query(project_slug, sql_content)
                console.print(f"[green]✓[/green] Database seeded from SQL file")
            else:
                # JSON seed file
                with open(file_path, 'r') as f:
                    seed_data = json.load(f)
                
                count = 0
                for table, rows in seed_data.items():
                    for row in rows:
                        api.insert_data(project_slug, table, row)
                        count += 1
                
                console.print(f"[green]✓[/green] Seeded {count} rows from JSON file")
        else:
            # Look for seed.sql in current directory
            seed_file = Path('seed.sql')
            if seed_file.exists():
                with open(seed_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                result = api.query(project_slug, sql_content)
                console.print(f"[green]✓[/green] Database seeded from seed.sql")
            else:
                console.print("[yellow]No seed file found. Use --file to specify a seed file.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('diff')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def diff_schema(ctx, project, fmt):
    """
    Compare local migration schema against the remote database schema.

    Parses CREATE TABLE statements from all unapplied migrations in
    the local migrations/ directory and compares them against the
    live remote schema.
    """
    import re

    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    # ── Get remote schema ────────────────────────────────────────────
    remote_schema = api.get_schema(project_slug)
    remote_tables = {t['name']: t for t in remote_schema.get('tables', [])}

    # ── Parse local migrations ───────────────────────────────────────
    migrations_dir = Path('migrations')
    local_tables: dict = {}

    if migrations_dir.exists():
        history = api.get_migration_history(project_slug)
        applied_names = {m['migration_name'] for m in history if not m.get('rolled_back_at')}

        for sql_file in sorted(migrations_dir.glob('*.sql')):
            if sql_file.stem in applied_names:
                continue
            sql = sql_file.read_text(encoding='utf-8')
            # Extract CREATE TABLE names from the UP file
            for match in re.finditer(
                r'CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+"?(\w+)"?',
                sql, re.IGNORECASE
            ):
                tname = match.group(1)
                local_tables[tname] = {'file': sql_file.name}
    else:
        console.print("[yellow]No migrations/ directory found. Showing remote schema only.[/yellow]")

    # ── Build diff ───────────────────────────────────────────────────
    differences = []

    for tname in local_tables:
        if tname not in remote_tables:
            differences.append({'type': 'TABLE', 'name': tname, 'status': 'PENDING', 'details': f"In {local_tables[tname]['file']} but not yet in remote"})

    for tname in remote_tables:
        if tname not in local_tables and tname not in {
            # ignore system tables
            'schema_migrations', 'migration_history', 'spatial_ref_sys'
        }:
            differences.append({'type': 'TABLE', 'name': tname, 'status': 'REMOTE_ONLY', 'details': 'Exists in remote but not in local migrations'})

    if fmt != 'table':
        format_output({'differences': differences, 'local_tables': list(local_tables.keys()), 'remote_tables': list(remote_tables.keys())}, fmt, console)
        return

    if not differences:
        console.print("[green]✓[/green] No schema differences — local migrations match remote.")
        return

    _display_schema_diff({'differences': differences})


def _display_schema_diff(diff_result: dict):
    """Display schema differences in a table."""
    from rich.table import Table
    
    table = Table(title="Schema Differences")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="gray")
    
    differences = diff_result.get('differences', [])
    for diff in differences:
        table.add_row(
            diff.get('type', ''),
            diff.get('name', ''),
            diff.get('status', ''),
            diff.get('details', '')
        )
    
    console.print(table)
    
    if not differences:
        console.print("\n[green]✓[/green] No schema differences found")


@db_group.group('schema')
def schema_group():
    """Schema management commands."""
    pass


@schema_group.command('dump')
@click.option('--output', type=click.Path(), help='Output file path (default: schema.sql)')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def dump_schema(ctx, output, project):
    """Export database schema only (no data)."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        output_path = Path(output) if output else Path('schema.sql')
        
        console.print(f"[cyan]Exporting schema...[/cyan]")
        dump_data = api.dump_database(project_slug, schema_only=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dump_data.get('sql', ''))
        
        console.print(f"[green]✓[/green] Schema exported to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@schema_group.command('diff')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def schema_diff(ctx, project, fmt):
    """Show schema differences (alias for db diff)."""
    ctx.invoke(diff_schema, project=project, fmt=fmt)


@db_group.command('connect')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def connect_database(ctx, project):
    """Connect to database interactively."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        # Get database connection info
        connection_info = api.get_database_connection(project_slug)
        
        console.print(f"[cyan]Database Connection Info:[/cyan]")
        console.print(f"  Host: {connection_info.get('host')}")
        console.print(f"  Port: {connection_info.get('port')}")
        console.print(f"  Database: {connection_info.get('database')}")
        console.print(f"  User: {connection_info.get('user')}")
        console.print()
        console.print(f"  [bold]Connect with psql:[/bold]")
        console.print(f"    psql -h {connection_info.get('host')} -p {connection_info.get('port')} "
                      f"-U {connection_info.get('user')} -d {connection_info.get('database')}")
        console.print()
        console.print(f"  [dim]Or use 'wowsql db query' to run SQL via the CLI.[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('explain')
@click.argument('sql')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def explain_query(ctx, sql, project, format):
    """Explain query execution plan."""
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        explain_result = api.explain_query(project_slug, sql)
        output_format = format or ctx.obj['output']
        format_output(explain_result, output_format, console)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('analyze')
@click.argument('table')
@click.option('--project', help='Project slug (overrides default)')
@click.pass_context
def analyze_table(ctx, table, project):
    """Analyze table and show planner statistics."""
    from rich.table import Table as RichTable
    try:
        api = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()
        
        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()
        
        result = api.analyze_table(project_slug, table)
        console.print(f"[green]✓[/green] Table '[bold]{table}[/bold]' analyzed — planner statistics updated\n")

        stats = result.get('stats', {})
        if stats:
            # ── Table overview ───────────────────────────────────────────────
            overview = RichTable(title="Table Statistics", show_header=True, header_style="bold cyan")
            overview.add_column("Metric", style="dim", min_width=28)
            overview.add_column("Value", min_width=20)

            def _fmt(v):
                if v is None:
                    return "[dim]never[/dim]"
                return str(v)

            overview.add_row("Row count (live)",       _fmt(stats.get("row_count")))
            overview.add_row("Dead tuples",            _fmt(stats.get("dead_tuples")))
            overview.add_row("Modified since analyze", _fmt(stats.get("modified_since_analyze")))
            overview.add_row("Sequential scans",       _fmt(stats.get("seq_scans")))
            overview.add_row("Index scans",            _fmt(stats.get("index_scans")))
            overview.add_row("Table size",             _fmt(stats.get("table_size")))
            overview.add_row("Indexes size",           _fmt(stats.get("indexes_size")))
            overview.add_row("Total size",             _fmt(stats.get("total_size")))
            overview.add_row("Last analyze",           _fmt(stats.get("last_analyze")))
            overview.add_row("Last autoanalyze",       _fmt(stats.get("last_autoanalyze")))
            overview.add_row("Last vacuum",            _fmt(stats.get("last_vacuum")))
            overview.add_row("Last autovacuum",        _fmt(stats.get("last_autovacuum")))
            console.print(overview)

        indexes = result.get('indexes', [])
        if indexes:
            console.print()
            idx_table = RichTable(title="Indexes", show_header=True, header_style="bold cyan")
            idx_table.add_column("Index",    min_width=30)
            idx_table.add_column("Columns",  min_width=20)
            idx_table.add_column("Primary",  min_width=8)
            idx_table.add_column("Unique",   min_width=8)
            idx_table.add_column("Scans",    min_width=8)
            idx_table.add_column("Size",     min_width=10)
            for idx in indexes:
                idx_table.add_row(
                    idx.get("index_name", ""),
                    idx.get("columns", ""),
                    "✓" if idx.get("is_primary") else "",
                    "✓" if idx.get("is_unique") else "",
                    str(idx.get("scans") or 0),
                    idx.get("index_size", ""),
                )
            console.print(idx_table)

        # ── Health hints ─────────────────────────────────────────────────────
        if stats:
            hints = []
            dead = stats.get("dead_tuples") or 0
            live = stats.get("row_count") or 0
            if live > 0 and dead / max(live, 1) > 0.1:
                hints.append(f"[yellow]⚠[/yellow]  Dead tuple ratio is high ({dead}/{live}). Consider running [bold]wowsql db optimize {table}[/bold] (VACUUM ANALYZE).")
            if not stats.get("last_analyze") and not stats.get("last_autoanalyze"):
                hints.append("[yellow]⚠[/yellow]  Table has never been analyzed before.")
            if stats.get("seq_scans", 0) > 1000 and not indexes:
                hints.append("[yellow]⚠[/yellow]  High sequential scan count with no indexes. Consider adding an index.")
            if hints:
                console.print()
                for h in hints:
                    console.print(h)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@db_group.command('optimize')
@click.argument('table')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def optimize_table(ctx, table, project, yes):
    """VACUUM ANALYZE a table — reclaim dead tuples and refresh planner stats."""
    from rich.table import Table as RichTable
    try:
        api    = ctx.obj['api']
        config = ctx.obj['config']
        project_slug = project or config.get_default_project()

        if not project_slug:
            console.print("[red]Error:[/red] No project specified. Use --project or set default project.")
            raise click.Abort()

        # ── Fetch current stats so the user can make an informed decision ────
        console.print(f"[dim]Fetching current stats for '[bold]{table}[/bold]'…[/dim]")
        try:
            preview = api.analyze_table(project_slug, table)
            stats   = preview.get('stats', {})
        except Exception:
            stats = {}

        if stats:
            live      = stats.get('row_count') or 0
            dead      = stats.get('dead_tuples') or 0
            mod       = stats.get('modified_since_analyze') or 0
            total_sz  = stats.get('total_size', 'unknown')
            dead_pct  = round(dead / max(live, 1) * 100, 1)

            preview_tbl = RichTable(title=f"Current state of '{table}'", show_header=True, header_style="bold cyan")
            preview_tbl.add_column("Metric",  style="dim", min_width=26)
            preview_tbl.add_column("Value",   min_width=16)
            preview_tbl.add_row("Live rows",                str(live))
            preview_tbl.add_row("Dead tuples",              f"{dead}  ({dead_pct}%)")
            preview_tbl.add_row("Modified since analyze",   str(mod))
            preview_tbl.add_row("Total size",               total_sz)
            console.print(preview_tbl)
            console.print()

            # ── What VACUUM ANALYZE will do ───────────────────────────────────
            console.print("[bold]VACUUM ANALYZE[/bold] will:")
            console.print(f"  • Reclaim space from [yellow]{dead}[/yellow] dead tuple(s) (~{dead_pct}% bloat)")
            console.print(f"  • Refresh planner statistics for [yellow]{live}[/yellow] live row(s)")
            if mod > 0:
                console.print(f"  • Update stats for [yellow]{mod}[/yellow] row(s) modified since last analyze")
            console.print()

        # ── Confirmation ─────────────────────────────────────────────────────
        if not yes:
            confirmed = click.confirm(
                f"Run VACUUM ANALYZE on '{table}'?", default=True
            )
            if not confirmed:
                console.print("[dim]Aborted.[/dim]")
                return

        console.print(f"[dim]Running VACUUM ANALYZE on '[bold]{table}[/bold]'…[/dim]")
        result = api.optimize_table(project_slug, table)

        console.print(f"\n[green]✓[/green] VACUUM ANALYZE complete on '[bold]{table}[/bold]'\n")

        before = result.get('before', {})
        after  = result.get('after',  {})

        if before and after:
            # ── Before / After comparison table ──────────────────────────────
            cmp = RichTable(title="Before → After", show_header=True, header_style="bold cyan")
            cmp.add_column("Metric",      style="dim",   min_width=24)
            cmp.add_column("Before",      style="red",   min_width=14)
            cmp.add_column("After",       style="green", min_width=14)
            cmp.add_column("Change",      min_width=16)

            def _delta(a, b, unit=""):
                if a is None or b is None:
                    return "[dim]—[/dim]"
                diff = b - a
                if diff == 0:
                    return "[dim]no change[/dim]"
                sign = "+" if diff > 0 else ""
                color = "red" if diff > 0 else "green"
                return f"[{color}]{sign}{diff}{unit}[/{color}]"

            def _size_delta(before_bytes, after_bytes):
                if before_bytes is None or after_bytes is None:
                    return "[dim]—[/dim]"
                diff = after_bytes - before_bytes
                if diff == 0:
                    return "[dim]no change[/dim]"
                abs_diff = abs(diff)
                if abs_diff >= 1024 * 1024:
                    label = f"{abs_diff / 1024 / 1024:.1f} MB"
                elif abs_diff >= 1024:
                    label = f"{abs_diff / 1024:.1f} kB"
                else:
                    label = f"{abs_diff} B"
                if diff < 0:
                    return f"[green]−{label} reclaimed[/green]"
                return f"[red]+{label} grown[/red]"

            cmp.add_row("Live rows",
                str(before.get('row_count', '?')),
                str(after.get('row_count', '?')),
                _delta(before.get('row_count'), after.get('row_count')))
            cmp.add_row("Dead tuples",
                str(before.get('dead_tuples', '?')),
                str(after.get('dead_tuples', '?')),
                _delta(before.get('dead_tuples'), after.get('dead_tuples')))
            cmp.add_row("Modified since analyze",
                str(before.get('modified_since_analyze', '?')),
                str(after.get('modified_since_analyze', '?')),
                _delta(before.get('modified_since_analyze'), after.get('modified_since_analyze')))
            cmp.add_row("Total size",
                before.get('total_size', '?'),
                after.get('total_size', '?'),
                _size_delta(before.get('total_bytes'), after.get('total_bytes')))
            cmp.add_row("Table size",
                before.get('table_size', '?'),
                after.get('table_size', '?'),
                "[dim]—[/dim]")
            cmp.add_row("Indexes size",
                before.get('indexes_size', '?'),
                after.get('indexes_size', '?'),
                "[dim]—[/dim]")
            console.print(cmp)

        reclaimed = result.get('reclaimed_bytes', 0)
        if reclaimed > 0:
            if reclaimed >= 1024 * 1024:
                label = f"{reclaimed / 1024 / 1024:.1f} MB"
            elif reclaimed >= 1024:
                label = f"{reclaimed / 1024:.1f} kB"
            else:
                label = f"{reclaimed} bytes"
            console.print(f"\n[green]✓[/green] Reclaimed [bold]{label}[/bold] of storage.")
        elif after:
            console.print("\n[dim]No storage was reclaimed — table was already clean.[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


# ─── CSV IMPORT ──────────────────────────────────────────────────────────────

@db_group.command('import-csv')
@click.argument('file', type=click.Path(exists=True, dir_okay=False))
@click.option('--table', '-t', required=True, help='Target table name')
@click.option('--delimiter', '-d', default=',', show_default=True, help='CSV delimiter character')
@click.option('--no-header', is_flag=True, help='CSV file has no header row (columns named col_1, col_2, ...)')
@click.option('--create-table', is_flag=True, help='Auto-create the table from CSV column headers (all TEXT columns)')
@click.option('--on-conflict', type=click.Choice(['error', 'ignore', 'replace']), default='error',
              show_default=True,
              help='What to do when a row violates a constraint:\n'
                   '  error   – abort on first conflict (default)\n'
                   '  ignore  – skip conflicting rows silently\n'
                   '  replace – upsert (requires a primary key)')
@click.option('--project', help='Project slug (overrides default)')
@click.option('--format', 'fmt', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def import_csv(ctx, file, table, delimiter, no_header, create_table, on_conflict, project, fmt):
    """
    Import data from a local CSV file into a database table.

    Reads the CSV from your device and inserts each row into the specified table.
    The table must already exist unless --create-table is passed.

    \b
    Examples:
      # Import into an existing table
      wowsql db import-csv ./users.csv --table users

      # Create the table automatically from headers (all TEXT columns)
      wowsql db import-csv ./products.csv --table products --create-table

      # Tab-separated file, skip duplicate rows
      wowsql db import-csv ./orders.tsv --table orders -d $'\\t' --on-conflict ignore

      # Upsert (update existing rows by primary key)
      wowsql db import-csv ./inventory.csv --table inventory --on-conflict replace
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    api    = ctx.obj['api']
    config = ctx.obj['config']
    project_slug = project or config.get_default_project()

    if not project_slug:
        console.print("[red]Error:[/red] No project specified. Use --project or set a default.")
        raise click.Abort()

    csv_path = Path(file)
    file_size_kb = csv_path.stat().st_size / 1024

    console.print(f"[cyan]Importing[/cyan] {csv_path.name} → [bold]{table}[/bold]  ({file_size_kb:.1f} KB)")

    csv_content = csv_path.read_text(encoding='utf-8')

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(f"Sending to server...", total=None)
        result = api.import_csv_table(
            project_slug,
            table=table,
            csv_content=csv_content,
            delimiter=delimiter,
            has_header=not no_header,
            create_table=create_table,
            on_conflict=on_conflict,
        )

    if result.get('success'):
        console.print(f"[green]Import completed[/green]")
        console.print(f"  [bold]Table:[/bold]         {result.get('table', table)}")
        console.print(f"  [bold]Columns:[/bold]       {', '.join(result.get('columns', []))}")
        console.print(f"  [bold]Rows inserted:[/bold] {result.get('rows_inserted', 0)}")
        skipped = result.get('rows_skipped', 0)
        if skipped:
            console.print(f"  [yellow]Rows skipped:[/yellow]  {skipped}")
        errs = result.get('errors', [])
        if errs:
            console.print(f"  [yellow]Errors (first {min(5,len(errs))}):[/yellow]")
            for err in errs[:5]:
                row_preview = str(err.get('row', ''))[:80]
                console.print(f"    [dim]- {err.get('error','')} | row: {row_preview}[/dim]")
    else:
        console.print(f"[red]Import failed.[/red]")
        for err in result.get('errors', []):
            console.print(f"  [red]•[/red] {err}")
        raise click.Abort()

