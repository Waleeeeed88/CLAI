"""Main shell implementation."""
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich import box
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
import re
from pathlib import Path
from typing import Optional

from agents.factory import Role
from core import Orchestrator, get_filesystem
from config import get_settings
from .constants import COMMANDS, ROLES, WORKFLOWS, MENTION_ALIASES, TEAM_MENTIONS
from .completer import MentionCompleter


console = Console()


class CLAIShell:
    def __init__(self):
        self.orchestrator = Orchestrator(verbose=False)
        self.fs = get_filesystem()
        self.current_role: Optional[Role] = None
        self.running = True
        self.last_response = None
        self.history_file = Path.home() / ".clai_history"
        self.completer = MentionCompleter()
    
    def print_banner(self):
        banner = """
╔═════════════════════════════════════════════════════════════════╗
║   ██████╗██╗      █████╗ ██╗                                    ║
║  ██╔════╝██║     ██╔══██╗██║     Command Line AI Team           ║
║  ██║     ██║     ███████║██║     Type 'help' for commands       ║
║  ╚██████╗███████╗██║  ██║██║                                    ║
║   ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝                                    ║
╚═════════════════════════════════════════════════════════════════╝
"""
        console.print(banner, style="bold blue")
    
    def print_help(self):
        console.print("\n[bold cyan]@Mentions[/bold cyan]")
        console.print("  @senior, @dev, @qa, @ba, @reviewer, @team")
        console.print("\n[bold cyan]Commands[/bold cyan]")
        console.print("  team, workflows, workflow <name>, config, clear, exit")
        console.print("\n[bold cyan]File I/O[/bold cyan]")
        console.print("  @dev write code > file.py   |   @qa review < code.py")
        console.print()
    
    def print_team(self):
        settings = get_settings()
        table = Table(title="🤖 AI Team", box=box.ROUNDED)
        table.add_column("Role", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        
        team = [
            ("Senior Dev", settings.senior_dev_model, "Anthropic"),
            ("Coder", settings.coder_model, "Anthropic"),
            ("Coder 2", settings.coder_model_2, "Google"),
            ("QA", settings.qa_model, "Google"),
            ("BA", settings.ba_model, "OpenAI"),
            ("Reviewer", settings.reviewer_model, "Anthropic"),
        ]
        for role, model, provider in team:
            table.add_row(role, model, provider)
        console.print()
        console.print(table)
        console.print()
    
    def print_workflows(self):
        table = Table(title="📋 Workflows", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Pipeline", style="green")
        
        workflows = [
            ("feature", "BA → Senior → Coder → QA"),
            ("review", "Reviewer → Senior"),
            ("bugfix", "QA → Senior → Coder"),
            ("architecture", "BA → Senior → QA"),
        ]
        for name, pipeline in workflows:
            table.add_row(name, pipeline)
        console.print()
        console.print(table)
        console.print()
    
    def _query_agent(self, role: Role, prompt_text: str, save_to: Optional[str] = None):
        with console.status(f"[bold blue]{role.value} thinking...[/bold blue]"):
            try:
                response = self.orchestrator.ask(role, prompt_text)
                self.last_response = response
                console.print()
                console.print(Panel(
                    Markdown(response.content),
                    title=f"[bold green]{role.value.upper()}[/bold green]",
                    subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
                    box=box.ROUNDED,
                ))
                console.print()
                if save_to:
                    self._save_to_file(response.content, save_to)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def _query_team(self, prompt_text: str):
        console.print("\n[bold blue]🤖 Asking the whole team...[/bold blue]\n")
        for role in [Role.SENIOR_DEV, Role.CODER, Role.QA, Role.BA]:
            with console.status(f"[bold blue]{role.value} thinking...[/bold blue]"):
                try:
                    response = self.orchestrator.ask(role, prompt_text)
                    console.print(Panel(
                        Markdown(response.content),
                        title=f"[bold green]{role.value.upper()}[/bold green]",
                        box=box.ROUNDED,
                    ))
                    console.print()
                except Exception as e:
                    console.print(f"[red]{role.value} error: {e}[/red]")
    
    def _save_to_file(self, content: str, filename: str):
        try:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            code_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"}
            code_match = re.search(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
            if code_match and filepath.suffix in code_extensions:
                filepath.write_text(code_match.group(1).strip())
            else:
                filepath.write_text(content)
            console.print(f"[green]✓ Saved to {filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving: {e}[/red]")
    
    def _load_file_context(self, filepath: str) -> str:
        path = Path(filepath)
        if not path.exists():
            console.print(f"[red]Not found: {filepath}[/red]")
            return ""
        if path.is_file():
            return f"\n\n---\nFile: {path.name}\n```\n{path.read_text()}\n```\n"
        if path.is_dir():
            context = f"\n\n---\nDirectory: {path}\n"
            for file in path.rglob("*"):
                if file.is_file() and file.suffix in {".py", ".js", ".ts", ".json", ".md", ".txt"}:
                    try:
                        context += f"\n### {file.relative_to(path)}\n```\n{file.read_text()}\n```\n"
                    except:
                        pass
            return context
        return ""
    
    def handle_mention(self, user_input: str):
        save_to = None
        if ">" in user_input:
            parts = user_input.split(">")
            user_input = parts[0].strip()
            save_to = parts[1].strip()
        
        file_context = ""
        if "<" in user_input:
            parts = user_input.split("<")
            user_input = parts[0].strip()
            file_context = self._load_file_context(parts[1].strip())
        
        mentions_found = []
        for mention, role in MENTION_ALIASES.items():
            if mention in user_input.lower():
                mentions_found.append((mention, role))
                user_input = re.sub(re.escape(mention), "", user_input, flags=re.IGNORECASE)
        
        is_team_query = any(tm in user_input.lower() for tm in TEAM_MENTIONS)
        if is_team_query:
            for tm in TEAM_MENTIONS:
                user_input = re.sub(re.escape(tm), "", user_input, flags=re.IGNORECASE)
        
        prompt_text = user_input.strip() + file_context
        if not prompt_text.strip():
            console.print("[yellow]What would you like to ask?[/yellow]")
            return
        
        if is_team_query:
            self._query_team(prompt_text)
        elif mentions_found:
            self._query_agent(mentions_found[0][1], prompt_text, save_to)
        else:
            console.print("[yellow]No @mention found. Try: @senior, @dev, @qa, @ba, @team[/yellow]")
    
    def handle_workflow(self, args: list):
        if not args:
            console.print("[red]Usage: workflow <name>[/red]")
            self.print_workflows()
            return
        
        workflow_name = args[0]
        if workflow_name not in WORKFLOWS:
            console.print(f"[red]Unknown workflow: {workflow_name}[/red]")
            return
        
        context = {}
        if workflow_name == "feature":
            context["requirement"] = Prompt.ask("[cyan]What feature?[/cyan]")
        elif workflow_name == "review":
            code_path = Prompt.ask("[cyan]File to review[/cyan]")
            try:
                context["code"] = Path(code_path).read_text()
            except Exception as e:
                console.print(f"[red]Can't read file: {e}[/red]")
                return
        elif workflow_name == "bugfix":
            context["bug_description"] = Prompt.ask("[cyan]Describe the bug[/cyan]")
            code_path = Prompt.ask("[cyan]Code file[/cyan]")
            try:
                context["code"] = Path(code_path).read_text()
            except Exception as e:
                console.print(f"[red]Can't read file: {e}[/red]")
                return
        elif workflow_name == "architecture":
            context["project_description"] = Prompt.ask("[cyan]Describe the project[/cyan]")
        
        console.print(f"\n[bold blue]🚀 Running {workflow_name} workflow...[/bold blue]\n")
        try:
            result = self.orchestrator.run_workflow(workflow_name, context)
            if result.status.value == "completed":
                console.print(f"[green]✓ Done in {result.duration:.2f}s[/green]\n")
                for step_name, response in result.outputs.items():
                    role_name = step_name.split("_")[-1].upper()
                    console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]", box=box.ROUNDED))
                    console.print()
            else:
                console.print("[red]✗ Workflow failed[/red]")
                for error in result.errors:
                    console.print(f"[red]  {error}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def handle_config(self):
        try:
            settings = get_settings()
            table = Table(title="🔑 API Keys", box=box.ROUNDED)
            table.add_column("Provider", style="cyan")
            table.add_column("Status")
            for provider, key in [("Anthropic", settings.anthropic_api_key), ("OpenAI", settings.openai_api_key), ("Google", settings.google_api_key)]:
                status = "[green]✓[/green]" if key.get_secret_value() else "[red]✗[/red]"
                table.add_row(provider, status)
            console.print()
            console.print(table)
            console.print()
        except Exception as e:
            console.print(f"[red]Config error: {e}[/red]")
    
    def handle_projects(self):
        projects = self.fs.list_projects()
        if not projects:
            console.print("[yellow]No projects yet. Create with: newproject <name>[/yellow]")
            return
        table = Table(title="📂 Projects", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        for project in projects:
            table.add_row(project)
        console.print()
        console.print(table)
        console.print()
    
    def handle_new_project(self, args: list):
        if not args:
            console.print("[yellow]Usage: newproject <name> [python|node|basic][/yellow]")
            return
        name = args[0]
        template = args[1] if len(args) > 1 else "python"
        result = self.fs.create_project(name, template)
        if result.success:
            console.print(f"[green]✓ Created {name}[/green]")
            console.print(self.fs.get_tree(name))
        else:
            console.print(f"[red]✗ {result.message}[/red]")
    
    def handle_files(self, args: list):
        path = args[0] if args else "."
        files = self.fs.list_directory(path)
        if not files:
            console.print(f"[yellow]Empty or not found: {path}[/yellow]")
            return
        console.print(f"\n[cyan]📁 {path}[/cyan]")
        for f in files:
            if f.is_dir:
                console.print(f"  [blue]📁 {f.name}/[/blue]")
            else:
                console.print(f"  📄 {f.name}")
        console.print()
    
    def handle_tree(self, args: list):
        path = args[0] if args else "."
        console.print(f"\n[cyan]{self.fs.get_tree(path)}[/cyan]\n")
    
    def handle_read_file(self, args: list):
        if not args:
            console.print("[yellow]Usage: readfile <path>[/yellow]")
            return
        result = self.fs.read_file(args[0])
        if result.success:
            ext = Path(args[0]).suffix.lstrip(".")
            syntax_map = {"py": "python", "js": "javascript", "json": "json", "md": "markdown"}
            syntax = syntax_map.get(ext, "")
            console.print(f"\n[cyan]📄 {args[0]}[/cyan]\n")
            if syntax:
                console.print(Syntax(result.data, syntax, theme="monokai", line_numbers=True))
            else:
                console.print(result.data)
            console.print()
        else:
            console.print(f"[red]✗ {result.message}[/red]")
    
    def get_prompt_text(self) -> str:
        if self.current_role:
            return f"clai ({self.current_role.value})> "
        return "clai> "
    
    def process_input(self, user_input: str):
        user_input = user_input.strip()
        if not user_input:
            return
        
        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if self.current_role and cmd not in COMMANDS:
            self._query_agent(self.current_role, user_input)
            return
        
        if cmd in ("exit", "quit"):
            self.running = False
            console.print("[yellow]Goodbye! 👋[/yellow]")
        elif cmd == "help":
            self.print_help()
        elif cmd == "team":
            self.print_team()
        elif cmd == "workflows":
            self.print_workflows()
        elif cmd == "config":
            self.handle_config()
        elif cmd == "clear":
            console.clear()
            self.print_banner()
        elif cmd == "workflow":
            self.handle_workflow(args)
        elif cmd == "history":
            for role, agent in self.orchestrator._agents.items():
                if agent.conversation_history:
                    console.print(f"\n[bold]{role.value}[/bold]: {len(agent.conversation_history)} messages")
        elif cmd == "save":
            if self.last_response and args:
                self._save_to_file(self.last_response.content, args[0])
            else:
                console.print("[yellow]Usage: save <filename>[/yellow]")
        elif cmd == "workspace":
            console.print(f"\n[cyan]📁 Workspace:[/cyan] {self.fs.workspace_root}\n")
        elif cmd == "projects":
            self.handle_projects()
        elif cmd == "newproject":
            self.handle_new_project(args)
        elif cmd == "files":
            self.handle_files(args)
        elif cmd == "tree":
            self.handle_tree(args)
        elif cmd == "readfile":
            self.handle_read_file(args)
        elif user_input.startswith("@") or "@" in user_input:
            self.handle_mention(user_input)
        else:
            console.print("[yellow]Tip: Use @mentions like @senior, @dev, @qa[/yellow]")
    
    def run(self):
        console.clear()
        self.print_banner()
        self.print_help()
        try:
            get_settings()
            console.print("[green]✓ Configuration loaded[/green]\n")
        except Exception as e:
            console.print(f"[red]⚠ Config error: {e}[/red]\n")
        
        while self.running:
            try:
                user_input = prompt(
                    self.get_prompt_text(),
                    completer=self.completer,
                    history=FileHistory(str(self.history_file)),
                )
                self.process_input(user_input)
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                self.running = False
                console.print("\n[yellow]Goodbye! 👋[/yellow]")


def main():
    shell = CLAIShell()
    shell.run()


if __name__ == "__main__":
    main()
