"""
AI Sales Agent — CLI entry point.

Usage:
    python run_agent.py

The script asks for three inputs, runs the full agent pipeline,
and displays each reasoning step's result as soon as it completes.

Requires:
    - ANTHROPIC_API_KEY in .env
    - Agent Memory API running: python start_api.py (optional but recommended)
"""

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

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

    try:
        run(company=company, persona=persona, product=product, console=console)

    except ValueError as e:
        console.print(f"\n  [red]✗ Agent error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n  [red]✗ Unexpected error:[/red] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
