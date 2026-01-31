"""CLI - Click-based command line interface."""
import click
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from agents.factory import Role
from core import Orchestrator
from config import get_settings


console = Console()


def get_orchestrator(verbose: bool = False) -> Orchestrator:
    return Orchestrator(verbose=verbose)


@click.group()
@click.option('--verbose', '-v', is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    """🤖 CLAI - Your AI Development Team"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('role', type=click.Choice(['senior_dev', 'coder', 'coder_2', 'qa', 'ba', 'reviewer']))
@click.argument('prompt', nargs=-1, required=True)
@click.option('--file', '-f', type=click.Path(exists=True))
@click.pass_context
def ask(ctx, role, prompt, file):
    """Ask a team member a question."""
    verbose = ctx.obj.get('verbose', False)
    if file:
        with open(file, 'r') as f:
            prompt_text = f.read()
    else:
        prompt_text = ' '.join(prompt)
    
    if not prompt_text.strip():
        console.print("[red]No prompt provided[/red]")
        sys.exit(1)
    
    with console.status(f"[bold blue]Asking {role}...[/bold blue]"):
        try:
            orchestrator = get_orchestrator(verbose)
            response = orchestrator.ask(Role(role), prompt_text)
            console.print()
            console.print(Panel(
                Markdown(response.content),
                title=f"[bold green]{role.upper()}[/bold green]",
                subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
            ))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.argument('workflow', type=click.Choice(['feature', 'review', 'bugfix', 'architecture']))
@click.option('--requirement', '-r')
@click.option('--code', '-c', type=click.Path(exists=True))
@click.option('--bug', '-b')
@click.pass_context
def workflow(ctx, workflow, requirement, code, bug):
    """Run a multi-agent workflow."""
    verbose = ctx.obj.get('verbose', False)
    context = {}
    
    if workflow == 'feature':
        context['requirement'] = requirement or click.prompt('Feature requirement')
    elif workflow == 'review':
        with open(code or click.prompt('Code file'), 'r') as f:
            context['code'] = f.read()
    elif workflow == 'bugfix':
        context['bug_description'] = bug or click.prompt('Bug description')
        with open(code or click.prompt('Code file'), 'r') as f:
            context['code'] = f.read()
    elif workflow == 'architecture':
        context['project_description'] = requirement or click.prompt('Project description')
    
    console.print(f"\n[bold blue]Running {workflow}...[/bold blue]\n")
    try:
        orchestrator = get_orchestrator(verbose)
        result = orchestrator.run_workflow(workflow, context)
        if result.status.value == 'completed':
            console.print(f"[green]✓ Done in {result.duration:.2f}s[/green]\n")
            for step_name, response in result.outputs.items():
                role_name = step_name.split('_')[-1].upper()
                console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]"))
                console.print()
        else:
            console.print("[red]✗ Failed[/red]")
            for error in result.errors:
                console.print(f"[red]  {error}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def team():
    """Show team members."""
    settings = get_settings()
    table = Table(title="🤖 AI Team")
    table.add_column("Role", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")
    
    for role, model, provider in [
        ("Senior Dev", settings.senior_dev_model, "Anthropic"),
        ("Coder", settings.coder_model, "Anthropic"),
        ("Coder 2", settings.coder_model_2, "Google"),
        ("QA", settings.qa_model, "Google"),
        ("BA", settings.ba_model, "OpenAI"),
        ("Reviewer", settings.reviewer_model, "Anthropic"),
    ]:
        table.add_row(role, model, provider)
    console.print()
    console.print(table)
    console.print()


@cli.command()
def workflows():
    """List available workflows."""
    table = Table(title="📋 Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Pipeline", style="green")
    
    for name, pipeline in [
        ("feature", "BA → Senior → Coder → QA"),
        ("review", "Reviewer → Senior"),
        ("bugfix", "QA → Senior → Coder"),
        ("architecture", "BA → Senior → QA"),
    ]:
        table.add_row(name, pipeline)
    console.print()
    console.print(table)
    console.print()


@cli.command()
def config():
    """Show configuration status."""
    try:
        settings = get_settings()
        
        table = Table(title="🔑 API Keys")
        table.add_column("Provider", style="cyan")
        table.add_column("Status")
        for provider, key in [("Anthropic", settings.anthropic_api_key), ("OpenAI", settings.openai_api_key), ("Google", settings.google_api_key)]:
            status = "[green]✓[/green]" if key.get_secret_value() else "[red]✗[/red]"
            table.add_row(provider, status)
        console.print()
        console.print(table)
        console.print()
        
        table = Table(title="🤖 Models")
        table.add_column("Role", style="cyan")
        table.add_column("Model", style="green")
        for role, model in [
            ("Senior Dev", settings.senior_dev_model),
            ("Coder", settings.coder_model),
            ("Coder 2", settings.coder_model_2),
            ("QA", settings.qa_model),
            ("BA", settings.ba_model),
            ("Reviewer", settings.reviewer_model),
        ]:
            table.add_row(role, model)
        console.print(table)
        console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('role', type=click.Choice(['senior_dev', 'coder', 'coder_2', 'qa', 'ba', 'reviewer']))
@click.pass_context
def chat(ctx, role):
    """Start interactive chat with a team member."""
    verbose = ctx.obj.get('verbose', False)
    orchestrator = get_orchestrator(verbose)
    role_enum = Role(role)
    
    console.print(f"\n[bold green]Chatting with {role}[/bold green]")
    console.print("[dim]Type 'exit' to quit[/dim]\n")
    
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() in ('exit', 'quit'):
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


if __name__ == '__main__':
    main()
