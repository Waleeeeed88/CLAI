"""CLI - Click-based command line interface."""
import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from agents.factory import AgentFactory, Role
from config import get_settings
from core import Orchestrator


console = Console()


def get_orchestrator(verbose: bool = False) -> Orchestrator:
    return Orchestrator(verbose=verbose)


def _step_label(step_name: str) -> str:
    parts = step_name.split("_")
    if len(parts) <= 2:
        return step_name.upper()
    return "_".join(parts[2:]).upper()


@click.group()
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    """CLAI - Your AI Development Team"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("role", type=click.Choice(["senior_dev", "coder", "coder_2", "qa", "ba", "reviewer"]))
@click.argument("prompt", nargs=-1, required=True)
@click.option("--file", "-f", type=click.Path(exists=True))
@click.pass_context
def ask(ctx, role, prompt, file):
    """Ask a team member a question."""
    verbose = ctx.obj.get("verbose", False)
    if file:
        with open(file, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    else:
        prompt_text = " ".join(prompt)

    if not prompt_text.strip():
        console.print("[red]No prompt provided[/red]")
        sys.exit(1)

    with console.status(f"[bold blue]Asking {role}...[/bold blue]"):
        try:
            orchestrator = get_orchestrator(verbose)
            response = orchestrator.ask(Role(role), prompt_text)
            console.print()
            console.print(
                Panel(
                    Markdown(response.content),
                    title=f"[bold green]{role.upper()}[/bold green]",
                    subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
                )
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.argument("workflow", type=click.Choice(["feature", "review", "bugfix", "architecture"]))
@click.option("--requirement", "-r")
@click.option("--code", "-c", type=click.Path(exists=True))
@click.option("--bug", "-b")
@click.pass_context
def workflow(ctx, workflow, requirement, code, bug):
    """Run a multi-agent workflow."""
    verbose = ctx.obj.get("verbose", False)
    context = {}

    if workflow == "feature":
        context["requirement"] = requirement or click.prompt("Feature requirement")
    elif workflow == "review":
        with open(code or click.prompt("Code file"), "r", encoding="utf-8") as f:
            context["code"] = f.read()
    elif workflow == "bugfix":
        context["bug_description"] = bug or click.prompt("Bug description")
        with open(code or click.prompt("Code file"), "r", encoding="utf-8") as f:
            context["code"] = f.read()
    elif workflow == "architecture":
        context["project_description"] = requirement or click.prompt("Project description")

    console.print(f"\n[bold blue]Running {workflow}...[/bold blue]\n")
    try:
        orchestrator = get_orchestrator(verbose)
        result = orchestrator.run_workflow(workflow, context)
        if result.status.value == "completed":
            console.print(f"[green]Done in {result.duration:.2f}s[/green]\n")
            for step_name, response in result.outputs.items():
                role_name = _step_label(step_name)
                console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]"))
                console.print()
        else:
            console.print("[red]Failed[/red]")
            for error in result.errors:
                console.print(f"[red]  {error}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def team():
    """Show team members."""
    table = Table(title="AI Team")
    table.add_column("Role", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")

    for role_name, role in [
        ("BA", Role.BA),
        ("QA", Role.QA),
        ("Senior Dev", Role.SENIOR_DEV),
        ("Coder", Role.CODER),
        ("Coder 2", Role.CODER_2),
        ("Reviewer", Role.REVIEWER),
    ]:
        provider, model = AgentFactory.get_role_runtime_config(role)
        table.add_row(role_name, model, provider.value)
    console.print()
    console.print(table)
    console.print()


@cli.command()
def workflows():
    """List available workflows."""
    table = Table(title="Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Pipeline", style="green")

    for name, pipeline in [
        ("feature", "BA -> QA -> Senior -> Coder -> Coder2"),
        ("review", "Reviewer -> Senior"),
        ("bugfix", "QA -> Senior -> Coder"),
        ("architecture", "BA -> Senior -> QA"),
    ]:
        table.add_row(name, pipeline)
    console.print()
    console.print(table)
    console.print()


@cli.command()
@click.pass_context
def stages(ctx):
    """List available stages."""
    verbose = ctx.obj.get("verbose", False)
    orchestrator = get_orchestrator(verbose)
    table = Table(title="Stages")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description", style="white")

    for stage_name, details in orchestrator.get_stages().items():
        table.add_row(
            stage_name,
            details.get("status", "placeholder"),
            details.get("description", ""),
        )

    console.print()
    console.print(table)
    console.print()


@cli.command()
@click.argument(
    "stage_name",
    type=click.Choice(
        [
            "planning_discussion",
            "architecture_alignment",
            "implementation_breakdown",
            "verification_hardening",
            "release_handoff",
        ]
    ),
)
@click.option("--topic", "-t")
@click.pass_context
def stage(ctx, stage_name, topic):
    """Run a stage."""
    verbose = ctx.obj.get("verbose", False)
    orchestrator = get_orchestrator(verbose)
    context = {}
    if stage_name == "planning_discussion":
        context["requirement"] = topic or click.prompt("Planning topic")

    console.print(f"\n[bold blue]Running stage: {stage_name}...[/bold blue]\n")
    try:
        result = orchestrator.run_stage(stage_name, context)
        if result.status.value == "completed":
            console.print(f"[green]Done in {result.duration:.2f}s[/green]\n")
            for step_name, response in result.outputs.items():
                role_name = _step_label(step_name)
                console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]"))
                console.print()
        else:
            console.print("[red]Failed[/red]")
            for error in result.errors:
                console.print(f"[red]  {error}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def config():
    """Show configuration status."""
    try:
        settings = get_settings()

        table = Table(title="API Keys")
        table.add_column("Provider", style="cyan")
        table.add_column("Status")
        for provider, key in [
            ("Anthropic", settings.anthropic_api_key),
            ("OpenAI", settings.openai_api_key),
            ("Google", settings.google_api_key),
        ]:
            status = "[green]OK[/green]" if key.get_secret_value() else "[red]Missing[/red]"
            table.add_row(provider, status)
        console.print()
        console.print(table)
        console.print()

        table = Table(title="Effective Routing")
        table.add_column("Role", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        for role_name, role in [
            ("BA", Role.BA),
            ("QA", Role.QA),
            ("Senior Dev", Role.SENIOR_DEV),
            ("Coder", Role.CODER),
            ("Coder 2", Role.CODER_2),
            ("Reviewer", Role.REVIEWER),
        ]:
            provider, model = AgentFactory.get_role_runtime_config(role)
            table.add_row(role_name, model, provider.value)
        console.print(table)
        console.print()

        if settings.role_model_overrides or settings.role_provider_overrides:
            table = Table(title="Override Maps")
            table.add_column("Type", style="cyan")
            table.add_column("Value", style="white")
            table.add_row("role_model_overrides", str(settings.role_model_overrides))
            table.add_row("role_provider_overrides", str(settings.role_provider_overrides))
            console.print(table)
            console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("role", type=click.Choice(["senior_dev", "coder", "coder_2", "qa", "ba", "reviewer"]))
@click.pass_context
def chat(ctx, role):
    """Start interactive chat with a team member."""
    verbose = ctx.obj.get("verbose", False)
    orchestrator = get_orchestrator(verbose)
    role_enum = Role(role)

    console.print(f"\n[bold green]Chatting with {role}[/bold green]")
    console.print("[dim]Type 'exit' to quit[/dim]\n")

    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input.strip():
                continue
            with console.status("[bold blue]Thinking...[/bold blue]"):
                response = orchestrator.ask(role_enum, user_input, include_history=True)
            console.print()
            console.print(Panel(Markdown(response.content), title=f"[bold green]{role.upper()}[/bold green]"))
            console.print()
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
