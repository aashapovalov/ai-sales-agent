"""
Display functions for the AI Sales Agent CLI.

All Rich terminal output lives here — pipeline.py imports these
and calls them after each step completes. Keeps pipeline logic
and display logic fully separated.
"""

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from agent.models import OutreachMessage, PainPoints, PersonaAnalysis


def display_step0(console: Console, past_events_count: int, company: str) -> None:
    console.print()
    if past_events_count:
        console.print(
            f"  [yellow]⚡ Memory:[/yellow] Found [bold]{past_events_count}[/bold] "
            f"prior event(s) for [bold]{company}[/bold] — used as context"
        )
    else:
        console.print(
            f"  [dim]◦ Memory: No prior events found for {company} — fresh start[/dim]"
        )


def display_step1(console: Console, analysis: PersonaAnalysis) -> None:
    console.print()
    console.print(Rule("[bold]Step 1 — Company & Persona Analysis[/bold]", style="blue"))
    console.print()
    console.print(f"  [bold]Company type:[/bold]  {analysis.company_type}")
    console.print(f"  [bold]Stage:[/bold]         {analysis.company_stage}")
    console.print(f"  [bold]Value driver:[/bold]  [green]{analysis.value_driver}[/green]")
    console.print(f"  [bold]Context:[/bold]       {analysis.business_context}")
    console.print()
    console.print("  [bold]Persona priorities:[/bold]")
    for priority in analysis.persona_priorities:
        console.print(f"    • {priority}")


def display_step2(console: Console, pain_points: PainPoints) -> None:
    console.print()
    console.print(Rule("[bold]Step 2 — Pain Point Identification[/bold]", style="blue"))
    console.print()
    console.print(f"  [bold]Top pain:[/bold]     [red]{pain_points.top_pain}[/red]")
    console.print(f"  [bold]Why anything:[/bold] {pain_points.why_anything}")
    console.print()
    console.print("  [bold]Pain points identified:[/bold]")
    for i, pp in enumerate(pain_points.pain_points, 1):
        console.print(f"\n  [bold cyan]{i}. {pp.title}[/bold cyan]")
        console.print(f"     {pp.description}")
        console.print(f"     [dim]Urgency: {pp.urgency_signal}[/dim]")


def display_step3(console: Console, message: OutreachMessage) -> None:
    console.print()
    console.print(Rule("[bold]Step 3 — Outreach Message[/bold]", style="blue"))
    console.print()
    console.print(f"  [bold]Hook used:[/bold]     {message.hook_used}")
    console.print(f"  [bold]Value driver:[/bold]  {message.value_driver_mapped}")
    console.print()
    message_text = Text()
    message_text.append(f"Subject: {message.subject_line}\n\n", style="bold")
    message_text.append(message.message_body)
    console.print(
        Panel(
            message_text,
            title="[bold green]Cold Outreach Message[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def display_saved(console: Console, saved_event_id, company: str) -> None:
    console.print()
    if saved_event_id:
        console.print(
            f"  [green]✓[/green] Saved to memory as event "
            f"[bold]#{saved_event_id}[/bold] — "
            f"will inform future outreach to [bold]{company}[/bold]"
        )
    else:
        console.print(
            "  [dim]◦ Memory API not running — results not saved. "
            "Start with: python start_api.py[/dim]"
        )
    console.print()
