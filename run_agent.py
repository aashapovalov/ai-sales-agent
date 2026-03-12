"""
AI Sales Agent — CLI entry point.

Usage:
    python run_agent.py

The script asks for three inputs, runs the full agent pipeline,
and displays the reasoning steps and final outreach message.

Requires:
    - ANTHROPIC_API_KEY in .env
    - Agent Memory API running: python start_api.py (optional but recommended)
"""

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint

from agent.pipeline import run

console = Console()


def prompt_input(label: str, hint: str = "") -> str:
    """Prompt the user for input with a styled label."""
    if hint:
        console.print(f"  [dim]{hint}[/dim]")
    value = console.input(f"  [bold cyan]{label}:[/bold cyan] ").strip()
    while not value:
        console.print("  [red]This field is required.[/red]")
        value = console.input(f"  [bold cyan]{label}:[/bold cyan] ").strip()
    return value


def display_results(result) -> None:
    """Display the full agent reasoning chain and final output."""

    # ── Memory status ──────────────────────────────────────────────────────────
    console.print()
    if result.used_past_context:
        console.print(
            f"  [yellow]⚡ Memory:[/yellow] Found [bold]{result.past_events_count}[/bold] "
            f"prior event(s) for [bold]{result.company}[/bold] — used as context"
        )
    else:
        console.print(
            f"  [dim]◦ Memory: No prior events found for {result.company} — fresh start[/dim]"
        )

    # ── Step 1 — Persona Analysis ──────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Step 1 — Company & Persona Analysis[/bold]", style="blue"))
    console.print()

    analysis = result.analysis
    console.print(f"  [bold]Company type:[/bold]  {analysis.company_type}")
    console.print(f"  [bold]Stage:[/bold]         {analysis.company_stage}")
    console.print(f"  [bold]Value driver:[/bold]  [green]{analysis.value_driver}[/green]")
    console.print(f"  [bold]Context:[/bold]       {analysis.business_context}")
    console.print()
    console.print("  [bold]Persona priorities:[/bold]")
    for priority in analysis.persona_priorities:
        console.print(f"    • {priority}")

    # ── Step 2 — Pain Points ───────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Step 2 — Pain Point Identification[/bold]", style="blue"))
    console.print()

    pain_points = result.pain_points
    console.print(f"  [bold]Top pain:[/bold] [red]{pain_points.top_pain}[/red]")
    console.print(f"  [bold]Why anything:[/bold] {pain_points.why_anything}")
    console.print()
    console.print("  [bold]Pain points identified:[/bold]")
    for i, pp in enumerate(pain_points.pain_points, 1):
        console.print(f"\n  [bold cyan]{i}. {pp.title}[/bold cyan]")
        console.print(f"     {pp.description}")
        console.print(f"     [dim]Urgency: {pp.urgency_signal}[/dim]")

    # ── Step 3 — Outreach Message ──────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold]Step 3 — Outreach Message[/bold]", style="blue"))
    console.print()

    message = result.message
    console.print(f"  [bold]Hook used:[/bold]      {message.hook_used}")
    console.print(f"  [bold]Value driver:[/bold]   {message.value_driver_mapped}")
    console.print()

    # Display the message in a panel
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

    # ── Save confirmation ──────────────────────────────────────────────────────
    console.print()
    if result.saved_event_id:
        console.print(
            f"  [green]✓[/green] Saved to memory as event "
            f"[bold]#{result.saved_event_id}[/bold] — "
            f"will inform future outreach to [bold]{result.company}[/bold]"
        )
    else:
        console.print(
            "  [dim]◦ Memory API not running — results not saved. "
            "Start with: python start_api.py[/dim]"
        )
    console.print()


def main() -> None:
    # ── Header ─────────────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            "[bold]AI Sales Agent[/bold]\n"
            "[dim]Multi-step reasoning → personalized outreach[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()

    # ── Collect inputs ─────────────────────────────────────────────────────────
    console.print("  [bold]Tell me about your target:[/bold]")
    console.print()

    company = prompt_input(
        "Company name",
        hint="e.g. Stripe, Notion, Linear"
    )
    persona = prompt_input(
        "Target persona",
        hint="e.g. VP Engineering, Head of Payments, CTO"
    )
    product = prompt_input(
        "Product description",
        hint="e.g. AI fraud detection platform, developer observability tool"
    )

    # ── Run pipeline ───────────────────────────────────────────────────────────
    console.print()
    console.print(Rule(style="dim"))
    console.print()
    console.print("  [dim]Running agent pipeline...[/dim]")

    try:
        result = run(company=company, persona=persona, product=product)
        display_results(result)

    except ValueError as e:
        console.print(f"\n  [red]✗ Agent error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n  [red]✗ Unexpected error:[/red] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
