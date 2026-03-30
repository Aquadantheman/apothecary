"""Apothecary CLI — analyze your substance stack from the terminal."""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apothecary.data.loader import SubstanceDatabase
from apothecary.engine.interaction_engine import analyze_stack
from apothecary.engine.timing_engine import generate_timeline
from apothecary.models.interaction import Severity, SEVERITY_ICONS

app = typer.Typer(
    name="apothecary",
    help="Your full stack, understood. Analyze drug-supplement interactions.",
    no_args_is_help=True,
)
console = Console()

# Default data directory (relative to package)
DEFAULT_DATA_DIR = Path(__file__).parent / "data" / "curated"


def _load_db(data_dir: Path | None = None) -> SubstanceDatabase:
    """Load the substance database."""
    path = data_dir or DEFAULT_DATA_DIR
    db = SubstanceDatabase()
    count = db.load_directory(path)
    return db


@app.command()
def analyze(
    stack_file: Path = typer.Argument(..., help="Path to a YAML file listing your substances"),
    data_dir: Path = typer.Option(None, "--data-dir", "-d", help="Custom data directory"),
):
    """Analyze a substance stack for interactions, depletions, and timing."""
    db = _load_db(data_dir)

    # Load user stack
    with open(stack_file) as f:
        raw = yaml.safe_load(f)

    substance_ids = raw.get("substances", raw.get("stack", []))
    if isinstance(substance_ids[0], dict):
        substance_ids = [s.get("id", s.get("substance_id")) for s in substance_ids]

    # Resolve substances
    substances = []
    missing = []
    for sid in substance_ids:
        s = db.get(sid)
        if s:
            substances.append(s)
        else:
            missing.append(sid)

    if missing:
        console.print(f"\n[yellow]⚠ Substances not found in database: {', '.join(missing)}[/yellow]")
        console.print(f"  Database has {db.count} substances loaded.\n")

    if not substances:
        console.print("[red]No valid substances found. Nothing to analyze.[/red]")
        raise typer.Exit(1)

    # Run analysis
    result = analyze_stack(substances)

    # === Display Results ===
    console.print()

    # Header
    substance_names = [s.name for s in substances]
    console.print(
        Panel(
            "\n".join(f"  • {name}" for name in substance_names),
            title="[bold]Analyzing Stack[/bold]",
            border_style="cyan",
        )
    )

    # Summary bar
    counts = result.interaction_count_by_severity
    summary_parts = []
    for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MODERATE, Severity.LOW, Severity.BENEFICIAL]:
        count = counts.get(sev.value, 0)
        if count > 0:
            summary_parts.append(f"{SEVERITY_ICONS[sev]} {sev.value.upper()}: {count}")
    console.print(f"\n  {'  |  '.join(summary_parts)}\n")

    # Aggregate metrics
    if result.aggregate_serotonin_load > 0:
        load = result.aggregate_serotonin_load
        color = "red" if load >= 0.9 else "yellow" if load >= 0.6 else "green"
        console.print(f"  Aggregate serotonin load: [{color}]{load:.2f}[/{color}] / 1.0")
    if result.aggregate_cardiovascular_flags > 1:
        console.print(
            f"  [yellow]Cardiovascular-flagged substances: {result.aggregate_cardiovascular_flags}[/yellow]"
        )
    console.print()

    # Interactions
    if result.interactions:
        console.print("[bold]Interactions[/bold]\n")
        for interaction in result.interactions:
            icon = SEVERITY_ICONS[interaction.severity]
            sev_color = {
                Severity.CRITICAL: "red",
                Severity.HIGH: "orange1",
                Severity.MODERATE: "yellow",
                Severity.LOW: "blue",
                Severity.BENEFICIAL: "green",
            }[interaction.severity]

            # Title line
            title_text = Text()
            title_text.append(f"  {icon} ", style="bold")
            title_text.append(f"[{interaction.severity.value.upper()}] ", style=f"bold {sev_color}")
            title_text.append(interaction.title, style="bold")
            console.print(title_text)

            # Substances involved
            console.print(f"     Substances: {', '.join(interaction.substances)}")

            # Type and confidence
            console.print(
                f"     Type: {interaction.type.value} | "
                f"Confidence: {interaction.confidence.value}"
            )

            # Mechanism
            console.print(f"     [dim]Mechanism:[/dim] {interaction.mechanism}")

            # Recommendation
            rec_style = "red" if interaction.severity == Severity.CRITICAL else "cyan"
            console.print(f"     [{rec_style}]→ {interaction.recommendation}[/{rec_style}]")

            # Timing suggestion if applicable
            if interaction.timing_relevant and interaction.timing_suggestion:
                console.print(f"     [green]⏰ {interaction.timing_suggestion}[/green]")

            console.print()

    # Depletion gaps
    if result.depletion_gaps:
        console.print("[bold]Nutrient Depletion Gaps[/bold]\n")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Nutrient", style="cyan")
        table.add_column("Depleted By")
        table.add_column("Significance")
        table.add_column("Suggestion", style="green")

        for gap in result.depletion_gaps:
            table.add_row(
                gap.nutrient,
                ", ".join(gap.depleted_by),
                gap.clinical_significance,
                gap.suggestion,
            )
        console.print(table)
        console.print()

    # Disclaimer
    console.print(
        Panel(
            "[dim]This report is for informational purposes only and does not constitute medical advice. "
            "Always consult a qualified healthcare professional before starting, stopping, or changing "
            "any medication or supplement.[/dim]",
            border_style="dim",
        )
    )


@app.command()
def timeline(
    stack_file: Path = typer.Argument(..., help="Path to a YAML file listing your substances"),
    wake_time: str = typer.Option("07:00", "--wake", "-w", help="Wake time (HH:MM)"),
    sleep_target: str = typer.Option("23:00", "--sleep", "-s", help="Target sleep time (HH:MM)"),
    data_dir: Path = typer.Option(None, "--data-dir", "-d", help="Custom data directory"),
):
    """Generate an optimized daily timing schedule for your stack."""
    db = _load_db(data_dir)

    # Load user stack
    with open(stack_file) as f:
        raw = yaml.safe_load(f)

    substance_ids = raw.get("substances", raw.get("stack", []))
    if isinstance(substance_ids[0], dict):
        substance_ids = [s.get("id", s.get("substance_id")) for s in substance_ids]

    # Resolve substances
    substances = []
    missing = []
    for sid in substance_ids:
        s = db.get(sid)
        if s:
            substances.append(s)
        else:
            missing.append(sid)

    if missing:
        console.print(f"\n[yellow]⚠ Substances not found in database: {', '.join(missing)}[/yellow]")

    if not substances:
        console.print("[red]No valid substances found.[/red]")
        raise typer.Exit(1)

    # Generate timeline
    tl = generate_timeline(substances, wake_time=wake_time, sleep_target=sleep_target)

    # Display
    console.print()
    console.print(
        Panel(
            f"Wake: [bold]{tl.wake_time}[/bold]  |  Sleep Target: [bold]{tl.sleep_target}[/bold]",
            title="[bold]Daily Timeline[/bold]",
            border_style="cyan",
        )
    )
    console.print()

    for block in tl.active_blocks:
        # Block header
        header = Text()
        header.append(f"  ⏰ {block.clock_time}", style="bold cyan")
        header.append(f"  —  {block.label}", style="bold")
        console.print(header)

        # Doses
        for dose in block.doses:
            console.print(f"     💊 [bold]{dose.substance_name}[/bold]")
            console.print(f"        [dim]{dose.rationale}[/dim]")
            if dose.food_note:
                console.print(f"        [green]🍽  {dose.food_note}[/green]")

        # Meal note for the block
        if block.meal_note:
            console.print(f"     [yellow]🥗 {block.meal_note}[/yellow]")

        console.print()

    # Global notes
    if tl.notes:
        console.print("[bold]General Notes[/bold]\n")
        for note in tl.notes:
            console.print(f"  • {note}")
        console.print()

    # Disclaimer
    console.print(
        Panel(
            "[dim]This schedule is for informational purposes only. Timing suggestions are based on "
            "published pharmacokinetic data and general principles. Individual responses vary. "
            "Discuss any changes with your prescriber.[/dim]",
            border_style="dim",
        )
    )


@app.command()
def info(
    substance: str = typer.Argument(..., help="Substance ID or name to look up"),
    data_dir: Path = typer.Option(None, "--data-dir", "-d", help="Custom data directory"),
):
    """Display detailed information about a substance."""
    db = _load_db(data_dir)

    # Try exact match first, then search
    s = db.get(substance)
    if not s:
        results = db.search(substance)
        if len(results) == 1:
            s = results[0]
        elif len(results) > 1:
            console.print(f"Multiple matches for '{substance}':")
            for r in results:
                console.print(f"  • {r.id}: {r.name}")
            return
        else:
            console.print(f"[red]No substance found for '{substance}'[/red]")
            return

    console.print()
    console.print(Panel(f"[bold]{s.name}[/bold]\nType: {s.type.value} | Category: {s.category}", border_style="cyan"))

    # CYP450
    if s.metabolism.cyp450:
        console.print("\n[bold]CYP450 Metabolism[/bold]")
        for entry in s.metabolism.cyp450:
            console.print(f"  • {entry.enzyme}: {entry.role.value} ({entry.significance.value}) [{entry.evidence.value}]")

    # Receptor activity
    if s.receptor_activity:
        console.print("\n[bold]Receptor Activity[/bold]")
        for ra in s.receptor_activity:
            console.print(f"  • {ra.system.value}: {ra.direction.value} ({ra.magnitude.value})")
            console.print(f"    {ra.mechanism}")

    # Nutrient depletions
    if s.nutrient_effects.depletions:
        console.print("\n[bold]Nutrient Depletions[/bold]")
        for dep in s.nutrient_effects.depletions:
            console.print(f"  • {dep.nutrient}: {dep.mechanism} [{dep.evidence.value}]")

    # Safety
    console.print("\n[bold]Safety Profile[/bold]")
    console.print(f"  Serotonin load: {s.safety.serotonin_load}")
    flags = []
    if s.safety.cardiovascular_flag:
        flags.append("cardiovascular")
    if s.safety.appetite_suppression:
        flags.append("appetite suppression")
    if s.safety.sleep_disruption:
        flags.append("sleep disruption")
    if flags:
        console.print(f"  Flags: {', '.join(flags)}")
    if s.safety.contraindications:
        console.print("  Contraindications:")
        for c in s.safety.contraindications:
            console.print(f"    ⚠ {c}")

    # Timing
    if s.timing.optimal_window:
        console.print(f"\n[bold]Timing[/bold]")
        console.print(f"  Optimal: {s.timing.optimal_window}")
        console.print(f"  Food: {s.timing.take_with_food.value}")
        for sp in s.timing.spacing_requirements:
            console.print(f"  • Space from {sp.substance_tag}: {sp.rule.value} — {sp.reason}")

    console.print()


@app.command()
def check(
    substance_a: str = typer.Argument(..., help="First substance ID"),
    substance_b: str = typer.Argument(..., help="Second substance ID"),
    data_dir: Path = typer.Option(None, "--data-dir", "-d", help="Custom data directory"),
):
    """Quick pairwise interaction check between two substances."""
    db = _load_db(data_dir)

    a = db.get(substance_a)
    b = db.get(substance_b)

    if not a:
        console.print(f"[red]Substance not found: {substance_a}[/red]")
        raise typer.Exit(1)
    if not b:
        console.print(f"[red]Substance not found: {substance_b}[/red]")
        raise typer.Exit(1)

    result = analyze_stack([a, b])

    console.print(f"\n[bold]Checking: {a.name} ↔ {b.name}[/bold]\n")

    if not result.interactions:
        console.print("[green]No known interactions found.[/green]")
        console.print("[dim]Note: Absence of known interactions does not guarantee safety.[/dim]")
    else:
        for interaction in result.interactions:
            icon = SEVERITY_ICONS[interaction.severity]
            console.print(f"  {icon} [{interaction.severity.value.upper()}] {interaction.title}")
            console.print(f"     {interaction.mechanism}")
            console.print(f"     → {interaction.recommendation}")
            console.print()

    console.print()


@app.command()
def list_substances(
    data_dir: Path = typer.Option(None, "--data-dir", "-d", help="Custom data directory"),
):
    """List all substances in the database."""
    db = _load_db(data_dir)

    table = Table(title=f"Substance Database ({db.count} substances)")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Category")
    table.add_column("CYP450")

    for s in db.all():
        cyp = ", ".join(f"{e.enzyme}({e.role.value[0]})" for e in s.metabolism.cyp450)
        table.add_row(s.id, s.name, s.type.value, s.category, cyp or "—")

    console.print(table)


if __name__ == "__main__":
    app()
