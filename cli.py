"""
CLAI - Command Line AI Team

Click-based CLI interface for interacting with the AI team.
"""
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from typing import Optional
import sys

from agents.factory import Role
from orchestrator import Orchestrator
from roles.base import list_roles


# Initialize Rich console for beautiful output
console = Console()


def get_orchestrator(verbose: bool = False) -> Orchestrator:
    """Get or create the orchestrator instance."""
    return Orchestrator(verbose=verbose)


# =============================================================================
# Main CLI Group
# =============================================================================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    🤖 CLAI - Your AI Development Team
    
    A CLI tool that orchestrates multiple AI models as a development team:
    
    \b
    • Senior Dev (Claude Opus) - Architecture & complex coding
    • Coder (GPT-4o) - Implementation & features
    • QA (GPT-4o) - Testing & bug finding
    • BA (Gemini) - Requirements & specifications
    • Reviewer (Claude Sonnet) - Fast code reviews
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


# =============================================================================
# Ask Command - Single Agent Queries
# =============================================================================

@cli.command()
@click.argument('role', type=click.Choice(['senior_dev', 'coder', 'qa', 'ba', 'reviewer']))
@click.argument('prompt', nargs=-1, required=True)
@click.option('--file', '-f', type=click.Path(exists=True), help='Read prompt from file')
@click.pass_context
def ask(ctx, role, prompt, file):
    """
    Ask a specific team member a question.
    
    \b
    Examples:
        clai ask senior_dev "Design a REST API for user management"
        clai ask coder "Implement a binary search in Python"
        clai ask qa "Review this code for bugs" -f code.py
    """
    verbose = ctx.obj.get('verbose', False)
    
    # Build prompt
    if file:
        with open(file, 'r') as f:
            prompt_text = f.read()
    else:
        prompt_text = ' '.join(prompt)
    
    if not prompt_text.strip():
        console.print("[red]Error: No prompt provided[/red]")
        sys.exit(1)
    
    # Get the role enum
    role_enum = Role(role)
    
    with console.status(f"[bold blue]Asking {role}...[/bold blue]"):
        try:
            orchestrator = get_orchestrator(verbose)
            response = orchestrator.ask(role_enum, prompt_text)
            
            # Display response
            console.print()
            console.print(Panel(
                Markdown(response.content),
                title=f"[bold green]{role.upper()}[/bold green]",
                subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
            ))
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if verbose:
                console.print_exception()
            sys.exit(1)


# =============================================================================
# Workflow Command - Multi-Agent Workflows
# =============================================================================

@cli.command()
@click.argument('workflow', type=click.Choice(['feature', 'review', 'bugfix', 'architecture']))
@click.option('--requirement', '-r', help='The requirement or description')
@click.option('--code', '-c', type=click.Path(exists=True), help='Code file for review/bugfix')
@click.option('--bug', '-b', help='Bug description for bugfix workflow')
@click.pass_context
def workflow(ctx, workflow, requirement, code, bug):
    """
    Run a multi-agent workflow.
    
    \b
    Workflows:
        feature      - BA → Senior Dev → Coder → QA
        review       - Reviewer → Senior Dev
        bugfix       - QA → Senior Dev → Coder
        architecture - BA → Senior Dev → QA
    
    \b
    Examples:
        clai workflow feature -r "User authentication with OAuth"
        clai workflow review -c app.py
        clai workflow bugfix -b "Login fails with special chars" -c auth.py
    """
    verbose = ctx.obj.get('verbose', False)
    
    # Build context based on workflow type
    context = {}
    
    if workflow == 'feature':
        if not requirement:
            requirement = click.prompt('Enter the feature requirement')
        context['requirement'] = requirement
        
    elif workflow == 'review':
        if not code:
            code = click.prompt('Enter the code file path')
        with open(code, 'r') as f:
            context['code'] = f.read()
            
    elif workflow == 'bugfix':
        if not bug:
            bug = click.prompt('Describe the bug')
        if not code:
            code = click.prompt('Enter the code file path')
        with open(code, 'r') as f:
            context['bug_description'] = bug
            context['code'] = f.read()
            
    elif workflow == 'architecture':
        if not requirement:
            requirement = click.prompt('Describe the project')
        context['project_description'] = requirement
    
    # Run workflow
    console.print(f"\n[bold blue]Running workflow: {workflow}[/bold blue]\n")
    
    try:
        orchestrator = get_orchestrator(verbose)
        result = orchestrator.run_workflow(workflow, context)
        
        # Display results
        if result.status.value == 'completed':
            console.print(f"[green]✓ Workflow completed in {result.duration:.2f}s[/green]\n")
            
            for step_name, response in result.outputs.items():
                role_name = step_name.split('_')[-1].upper()
                console.print(Panel(
                    Markdown(response.content),
                    title=f"[bold]{role_name}[/bold]",
                    subtitle=f"[dim]{response.model}[/dim]",
                ))
                console.print()
        else:
            console.print(f"[red]✗ Workflow failed[/red]")
            for error in result.errors:
                console.print(f"[red]  {error}[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


# =============================================================================
# Team Command - Team Information
# =============================================================================

@cli.command()
def team():
    """Show the AI team members and their capabilities."""
    table = Table(title="🤖 AI Team Members")
    
    table.add_column("Role", style="cyan", no_wrap=True)
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")
    table.add_column("Description", style="white")
    
    from config import get_settings
    settings = get_settings()
    
    team_info = [
        ("Senior Dev", settings.senior_dev_model, "Anthropic", "Architecture, complex coding, code review"),
        ("Coder", settings.coder_model, "OpenAI", "Implementation, features, rapid coding"),
        ("QA", settings.qa_model, "OpenAI", "Testing, bug finding, quality"),
        ("BA", settings.ba_model, "Google", "Requirements, specs, analysis"),
        ("Reviewer", settings.reviewer_model, "Anthropic", "Fast code reviews, feedback"),
    ]
    
    for role, model, provider, desc in team_info:
        table.add_row(role, model, provider, desc)
    
    console.print()
    console.print(table)
    console.print()


# =============================================================================
# Workflows Command - List Workflows
# =============================================================================

@cli.command()
def workflows():
    """List available workflows."""
    table = Table(title="📋 Available Workflows")
    
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Steps", style="green")
    table.add_column("Description", style="white")
    
    workflow_info = [
        ("feature", "BA → Senior Dev → Coder → QA", "Full feature development pipeline"),
        ("review", "Reviewer → Senior Dev", "Code review with improvement suggestions"),
        ("bugfix", "QA → Senior Dev → Coder", "Analyze and fix bugs"),
        ("architecture", "BA → Senior Dev → QA", "Architecture design and review"),
    ]
    
    for name, steps, desc in workflow_info:
        table.add_row(name, steps, desc)
    
    console.print()
    console.print(table)
    console.print()


# =============================================================================
# Config Command - Configuration Status
# =============================================================================

@cli.command()
def config():
    """Show current configuration status."""
    from config import get_settings
    
    console.print("\n[bold]Configuration Status[/bold]\n")
    
    try:
        settings = get_settings()
        
        # API Keys status
        table = Table(title="🔑 API Keys")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        
        api_keys = [
            ("Anthropic", bool(settings.anthropic_api_key.get_secret_value())),
            ("OpenAI", bool(settings.openai_api_key.get_secret_value())),
            ("Google", bool(settings.google_api_key.get_secret_value())),
        ]
        
        for provider, configured in api_keys:
            status = "[green]✓ Configured[/green]" if configured else "[red]✗ Missing[/red]"
            table.add_row(provider, status)
        
        console.print(table)
        console.print()
        
        # Model configuration
        table = Table(title="🤖 Model Configuration")
        table.add_column("Role", style="cyan")
        table.add_column("Model", style="green")
        
        models = [
            ("Senior Dev", settings.senior_dev_model),
            ("Coder", settings.coder_model),
            ("QA", settings.qa_model),
            ("BA", settings.ba_model),
            ("Reviewer", settings.reviewer_model),
        ]
        
        for role, model in models:
            table.add_row(role, model)
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {str(e)}[/red]")
        console.print("[yellow]Make sure you have a .env file with your API keys[/yellow]")
        sys.exit(1)


# =============================================================================
# Chat Command - Interactive Chat
# =============================================================================

@cli.command()
@click.argument('role', type=click.Choice(['senior_dev', 'coder', 'qa', 'ba', 'reviewer']))
@click.pass_context
def chat(ctx, role):
    """
    Start an interactive chat session with a team member.
    
    Type 'exit' or 'quit' to end the session.
    Type 'clear' to clear conversation history.
    """
    verbose = ctx.obj.get('verbose', False)
    orchestrator = get_orchestrator(verbose)
    role_enum = Role(role)
    
    console.print(f"\n[bold green]Starting chat with {role}[/bold green]")
    console.print("[dim]Type 'exit' to quit, 'clear' to reset conversation[/dim]\n")
    
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            
            if user_input.lower() in ('exit', 'quit'):
                console.print("[yellow]Ending chat session[/yellow]")
                break
            
            if user_input.lower() == 'clear':
                orchestrator.clear_context(role_enum)
                console.print("[yellow]Conversation cleared[/yellow]")
                continue
            
            if not user_input.strip():
                continue
            
            with console.status("[bold blue]Thinking...[/bold blue]"):
                response = orchestrator.ask(role_enum, user_input, include_history=True)
            
            console.print()
            console.print(Panel(
                Markdown(response.content),
                title=f"[bold green]{role.upper()}[/bold green]",
                subtitle=f"[dim]{response.total_tokens} tokens[/dim]",
            ))
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if verbose:
                console.print_exception()


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
