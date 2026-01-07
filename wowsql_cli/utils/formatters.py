"""Output formatting utilities."""

import json
import yaml
from typing import Any, Dict, List
from rich.console import Console
from rich.table import Table
from rich.json import JSON

console = Console()


def format_output(data: Any, output_format: str, console: Console = console):
    """Format output based on format type."""
    if output_format == 'json':
        console.print(JSON(json.dumps(data, default=str)))
    elif output_format == 'yaml':
        console.print(yaml.dump(data, default_flow_style=False))
    else:
        # Default to table format
        format_table(data, console)


def format_table(data: Any, console: Console = console):
    """Format data as a table."""
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            # List of dictionaries
            table = Table(box=None)  # Use simple box for better Windows compatibility
            
            # For projects, show only key fields
            if 'slug' in data[0] and 'name' in data[0]:
                # This looks like projects data
                table.add_column("Name", style="cyan")
                table.add_column("Slug", style="magenta")
                table.add_column("Status", style="green")
                table.add_column("Created", style="yellow")
                
                for item in data:
                    status = "Active" if item.get('is_active', True) else "Inactive"
                    created = item.get('created_at', '')[:10] if item.get('created_at') else ''
                    table.add_row(
                        str(item.get('name', '')),
                        str(item.get('slug', '')),
                        status,
                        created
                    )
            else:
                # For other data, show all keys but limit columns
                keys = list(data[0].keys())
                # Limit to first 10 columns to avoid overflow
                keys = keys[:10]
                for key in keys:
                    table.add_column(key, style="cyan", overflow="fold")
                
                for item in data:
                    row_values = []
                    for k in keys:
                        val = item.get(k, '')
                        # Truncate long values
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val)[:50] + '...' if len(json.dumps(val)) > 50 else json.dumps(val)
                        elif len(str(val)) > 50:
                            val = str(val)[:50] + '...'
                        row_values.append(str(val))
                    table.add_row(*row_values)
            
            console.print(table)
        else:
            # Simple list
            for item in data:
                console.print(f"  • {item}")
    elif isinstance(data, dict):
        # Dictionary - show as key-value pairs
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2, default=str)
            table.add_row(str(key), str(value))
        
        console.print(table)
    else:
        console.print(str(data))


def format_query_results(data: Dict[str, Any], console: Console = console):
    """Format SQL query results as a table."""
    if 'data' not in data:
        console.print("[yellow]No data returned[/yellow]")
        return
    
    rows = data['data']
    if not rows:
        console.print("[yellow]No rows returned[/yellow]")
        return
    
    # Create table
    table = Table()
    
    # Add columns from first row
    if isinstance(rows[0], dict):
        for key in rows[0].keys():
            table.add_column(key, style="cyan")
        
        # Add rows
        for row in rows:
            table.add_row(*[str(row.get(k, '')) for k in rows[0].keys()])
    
    console.print(table)
    
    # Show count if available
    if 'count' in data:
        console.print(f"\n[dim]{data['count']} row(s) returned[/dim]")

