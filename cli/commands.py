import asyncio
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from job_finder.config import load_config, save_config, AppConfig
from job_finder.services.scheduler import SchedulerService
from job_finder.services.exporter import ExporterService
from job_finder.services.verifier import VerifierService
from job_finder.utils.dates import is_within_days
from job_finder.utils.logger import get_logger

logger = get_logger()
console = Console()
app = typer.Typer(help="🚀 Job Finder Bot - Autonomous Multi-Source Software & AI Job Search CLI")

@app.command()
def search():
    """
    🔍 Runs a complete search across all enabled sources, verifies listings, and exports results.
    """
    console.print("\n[bold cyan]🚀 Starting Job Finder Bot Search Engine...[/bold cyan]\n")
    config = load_config()

    scheduler = SchedulerService(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[yellow]Scraping & Verifying Job Opportunities...", total=None)
        results = asyncio.run(scheduler.run_pipeline())
        progress.update(task, completed=100, description="[green]Search and verification complete!")

    console.print("\n[bold green]✅ Search Finished Successfully![/bold green]")
    
    # Display Summary Panel
    panel_text = (
        f"[bold white]Total Database Jobs:[/bold white] [cyan]{results['total_jobs']}[/cyan]\n"
        f"[bold white]New Jobs Discovered:[/bold white] [bold green]+{results['new_jobs']}[/bold green]\n"
        f"[bold white]Candidate Jobs Scraped:[/bold white] [yellow]{results['scraped_count']}[/yellow]\n"
        f"[bold white]Data Saved To:[/bold white] [italic]data/jobs.csv & data/jobs.json[/italic]\n"
        f"[bold white]Intelligence Report:[/bold white] [italic]data/reports/report.md[/italic]"
    )
    console.print(Panel(panel_text, title="📊 Search Execution Summary", border_style="cyan"))

@app.command()
def verify():
    """
    🛡️ Re-check legitimacy and HTTP availability of stored jobs in the database.
    """
    console.print("\n[bold cyan]🛡️ Re-verifying stored jobs in database...[/bold cyan]\n")
    config = load_config()
    exporter = ExporterService()
    verifier = VerifierService(config)

    jobs = exporter.load_jobs_json()
    if not jobs:
        console.print("[yellow]No jobs currently stored in database.[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[yellow]Verifying {len(jobs)} stored jobs...", total=None)
        verified_jobs = asyncio.run(verifier.verify_jobs(jobs))
        progress.update(task, completed=100, description="[green]Verification finished!")

    exporter.save_jobs(verified_jobs)
    exporter.generate_report(verified_jobs, 0)
    console.print("[bold green]✅ Verification complete! Updated jobs database and report.[/bold green]")

@app.command()
def stats():
    """
    📈 Display comprehensive statistics (Total jobs, New jobs, Jobs by company/source/location).
    """
    exporter = ExporterService()
    jobs = exporter.load_jobs_json()
    if not jobs:
        console.print("[yellow]No jobs stored in database. Run 'jobfinder search' first.[/yellow]")
        return

    console.print(f"\n[bold cyan]📈 Job Finder Bot Statistics (Total: {len(jobs)})[/bold cyan]\n")

    # Table 1: Top Companies
    comp_counts = {}
    source_counts = {}
    loc_counts = {}

    for j in jobs:
        comp_counts[j.company] = comp_counts.get(j.company, 0) + 1
        source_counts[j.source] = source_counts.get(j.source, 0) + 1
        loc_counts[j.location] = loc_counts.get(j.location, 0) + 1

    table_comp = Table(title="🏢 Top Hiring Companies", header_style="bold magenta")
    table_comp.add_column("Company", style="white")
    table_comp.add_column("Open Positions", style="green", justify="right")
    for comp, cnt in sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        table_comp.add_row(comp, str(cnt))

    table_src = Table(title="🌐 Jobs by Source", header_style="bold blue")
    table_src.add_column("Source Platform", style="white")
    table_src.add_column("Jobs Found", style="cyan", justify="right")
    for src, cnt in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        table_src.add_row(src, str(cnt))

    table_loc = Table(title="📍 Jobs by Location", header_style="bold yellow")
    table_loc.add_column("Location", style="white")
    table_loc.add_column("Count", style="yellow", justify="right")
    for loc, cnt in sorted(loc_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        table_loc.add_row(loc, str(cnt))

    console.print(table_comp)
    console.print()
    console.print(table_src)
    console.print()
    console.print(table_loc)

@app.command()
def export():
    """
    📁 Force export database to CSV, JSON, and Markdown report formats.
    """
    exporter = ExporterService()
    jobs = exporter.load_jobs_json()
    if not jobs:
        console.print("[yellow]No jobs to export.[/yellow]")
        return

    exporter.save_jobs(jobs)
    report_path = exporter.generate_report(jobs, 0)
    console.print(f"[bold green]✅ Export complete! CSV, JSON, and Markdown report generated at {report_path}[/bold green]")

@app.command()
def clean():
    """
    🧹 Remove duplicate entries and expired jobs older than posting_age_days.
    """
    config = load_config()
    exporter = ExporterService()
    jobs = exporter.load_jobs_json()
    initial_count = len(jobs)

    if not jobs:
        console.print("[yellow]Database is empty.[/yellow]")
        return

    # Filter out expired jobs
    fresh_jobs = [j for j in jobs if is_within_days(j.posting_date, max_days=config.posting_age_days)]

    # Deduplicate remaining
    seen_ids = set()
    cleaned_jobs = []
    for j in fresh_jobs:
        if j.id not in seen_ids:
            seen_ids.add(j.id)
            cleaned_jobs.append(j)

    removed = initial_count - len(cleaned_jobs)
    exporter.save_jobs(cleaned_jobs)
    exporter.generate_report(cleaned_jobs, 0)

    console.print(f"[bold green]🧹 Cleaning complete! Removed {removed} expired or duplicate jobs. {len(cleaned_jobs)} retained.[/bold green]")

@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Display current configuration settings"),
    edit_keywords: Optional[str] = typer.Option(None, "--keywords", help="Comma-separated list of keywords"),
    edit_posting_age: Optional[int] = typer.Option(None, "--posting-age", help="Maximum posting age in days"),
    edit_remote_only: Optional[bool] = typer.Option(None, "--remote-only", help="Filter for remote jobs only"),
):
    """
    ⚙️ View and modify configuration settings without editing source code.
    """
    cfg = load_config()

    if edit_keywords:
        cfg.keywords = [k.strip() for k in edit_keywords.split(",") if k.strip()]
        save_config(cfg)
        console.print(f"[bold green]Updated keywords to: {cfg.keywords}[/bold green]")

    if edit_posting_age is not None:
        cfg.posting_age_days = edit_posting_age
        save_config(cfg)
        console.print(f"[bold green]Updated posting age limit to {cfg.posting_age_days} days.[/bold green]")

    if edit_remote_only is not None:
        cfg.remote_only = edit_remote_only
        save_config(cfg)
        console.print(f"[bold green]Updated remote-only to {cfg.remote_only}.[/bold green]")

    if show or (not edit_keywords and edit_posting_age is None and edit_remote_only is None):
        console.print("\n[bold cyan]⚙️ Current Configuration Settings[/bold cyan]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="white")
        table.add_column("Value", style="cyan")

        table.add_row("Keywords", ", ".join(cfg.keywords))
        table.add_row("Locations", ", ".join(cfg.locations))
        table.add_row("Posting Age Limit (Days)", str(cfg.posting_age_days))
        table.add_row("Remote Only", str(cfg.remote_only))
        table.add_row("Enabled Sources", ", ".join(cfg.enabled_sources))
        table.add_row("Fuzzy Threshold", f"{cfg.fuzzy_threshold}%")

        console.print(table)
