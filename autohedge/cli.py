"""
AutoHedge CLI — welcome screen and interactive REPL.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box

from autohedge.env_loader import load_env, require_openai_key
from autohedge.backends import resolve_llm_backend

load_env()

try:
    from importlib.metadata import version as _version

    VERSION = _version("autohedge")
except Exception:
    VERSION = "0.1.2"

console = Console()

# ASCII art: minimal "hedge" / chart vibe
BANNER_ART = r"""
    ▄▄▄▄▄▄▄
   █████████
  ▐▀▄▄▄▄▄▀▌
     ▀ ▀
  ▄▄ ▀▄▀ ▄▄
"""

TIPS = [
    (
        "Enter a task prompt to run (e.g. 'Analyze NVDA for 50k"
        " allocation')"
    ),
    "Type 'quit' or 'exit' to leave",
    "Type 'help' or '?' for commands",
]

RECENT_FILE = Path.home() / ".autohedge" / "recent_tasks.txt"
MAX_RECENT = 5


def _get_recent_tasks() -> list[str]:
    if not RECENT_FILE.exists():
        return []
    try:
        lines = RECENT_FILE.read_text().strip().splitlines()
        return [
            ln.strip() for ln in lines[-MAX_RECENT:] if ln.strip()
        ]
    except Exception:
        return []


def _append_recent(task: str) -> None:
    try:
        RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        recent = _get_recent_tasks()
        if task in recent:
            recent.remove(task)
        recent.append(task)
        RECENT_FILE.write_text("\n".join(recent[-MAX_RECENT:]))
    except Exception:
        pass


def _welcome() -> None:
    cwd = Path.cwd()
    try:
        cwd_str = cwd.relative_to(Path.home())
        cwd_display = f"~/{cwd_str}"
    except ValueError:
        cwd_display = str(cwd)

    welcome = Text("Welcome to AutoHedge", style="bold orange1")
    subtitle = Text(
        f"v{VERSION} · {cwd_display}",
        style="dim",
    )

    tips_text = Text(
        "Tips for getting started\n", style="bold orange1"
    )
    tips_text.append(" — ".join(TIPS), style="dim")

    recent = _get_recent_tasks()
    recent_heading = Text("Recent activity\n", style="bold orange1")
    if recent:
        recent_body = Text("\n".join(recent[-3:]), style="dim")
    else:
        recent_body = Text("No recent activity", style="dim")

    left = Text()
    left.append(welcome)
    left.append("\n\n")
    left.append(BANNER_ART, style="cyan")
    left.append("\n")
    left.append(subtitle)

    right = Text()
    right.append(tips_text)
    right.append("\n")
    right.append("─" * 50 + "\n", style="dim")
    right.append(recent_heading)
    right.append(recent_body)

    # Two-column layout inside one panel (Claude Code style)
    left_panel = Panel(
        left,
        box=box.MINIMAL,
        padding=(0, 1),
        border_style="dim",
        expand=False,
    )
    right_panel = Panel(
        right,
        box=box.MINIMAL,
        padding=(0, 1),
        border_style="dim",
        expand=True,
    )
    cols = Columns(
        [left_panel, right_panel], expand=True, equal=False
    )
    console.print(
        Panel(
            cols,
            title=f"[bold]AutoHedge v{VERSION}[/]",
            title_align="left",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def run_repl(llm_backend=None, codex_config=None) -> None:
    llm_backend = resolve_llm_backend(llm_backend)
    _welcome()
    if llm_backend == "codex":
        console.print(
            "[yellow]Codex research mode: provide data in your task. "
            "No live search or order execution.[/]"
        )

    while True:
        try:
            prompt = Text("> ", style="bold cyan")
            console.print(prompt, end="")
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/]")
            break

        if not line:
            continue

        lower = line.lower()
        if lower in ("quit", "exit", "q"):
            console.print("[dim]Goodbye.[/]")
            break

        if lower in ("help", "?", "h"):
            for t in TIPS:
                console.print(f"  [dim]·[/] {t}")
            continue

        # Treat as task prompt
        task = line
        _append_recent(task)
        try:
            from autohedge import AutoHedge

            system = AutoHedge(
                llm_backend=llm_backend, codex_config=codex_config
            )
            console.print("[dim]Running...[/]")
            result = system.run(task=task)
            console.print(
                Panel(
                    str(result)[:2000],
                    title="Result",
                    border_style="green",
                )
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autohedge",
        description=(
            "AutoHedge — interactive REPL for running research and"
            " hedging tasks."
        ),
        epilog="""
Commands (when running the REPL):
  <task>     Run a task (e.g. 'Analyze NVDA for 50k allocation')
  help, ?, h Show in-REPL tips
  quit, exit, q  Exit the REPL

Examples:
  autohedge              Start the interactive REPL
  autohedge help         Show this help
  autohedge --help       Show this help
  autohedge --version    Show version
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--llm-backend",
        choices=("litellm", "codex"),
        help=(
            "Backend (or AUTOHEDGE_LLM_BACKEND; default: litellm)."
            " Codex is research only."
        ),
    )
    parser.add_argument(
        "--codex-model",
        help=(
            "Codex model (or AUTOHEDGE_CODEX_MODEL; default: CLI"
            " default)."
        ),
    )
    parser.add_argument(
        "--codex-timeout",
        type=float,
        help=(
            "Seconds per Codex stage (or AUTOHEDGE_CODEX_TIMEOUT;"
            " default: 180)."
        ),
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program version and exit.",
    )
    return parser


def main() -> None:
    """Entry point for the AutoHedge CLI."""
    parser = _build_parser()
    # Treat bare "help" as --help (e.g. "autohedge help")
    if len(sys.argv) == 2 and sys.argv[1].lower() == "help":
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()  # exits on --help / --version
    try:
        backend = resolve_llm_backend(args.llm_backend)
    except ValueError as error:
        parser.error(str(error))
    config = {}
    if args.codex_model is not None:
        config["model"] = args.codex_model
    if args.codex_timeout is not None:
        config["timeout"] = args.codex_timeout
    if config and backend != "codex":
        parser.error(
            "--codex-model/--codex-timeout require --llm-backend"
            " codex"
        )
    if backend == "litellm" and not require_openai_key():
        console.print(
            "[yellow]Warning: OPENAI_API_KEY not set. Set it in .env"
            " or export it.[/]"
        )
    run_repl(llm_backend=backend, codex_config=config or None)
    sys.exit(0)


if __name__ == "__main__":
    main()
