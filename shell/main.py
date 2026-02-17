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
import time
from pathlib import Path
from typing import Optional

from agents.factory import AgentFactory, Role
from core import Orchestrator, get_filesystem
from core.pipeline import ProjectPipeline, PhaseResult, PhaseStatus
from config import get_settings
from .constants import COMMANDS, ROLES, WORKFLOWS, STAGES, MENTION_ALIASES, TEAM_MENTIONS
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
        console.print("  @team runs BA-first roundtable discussion")
        console.print("\n[bold cyan]Commands[/bold cyan]")
        console.print("  team, workflows, workflow <name>, stages, stage <name>, config, clear, exit")
        console.print("  tools [role]             # List tools available to agents")
        console.print("  github                   # GitHub MCP status & tools")
        console.print("\n[bold cyan]Project Pipeline[/bold cyan]")
        console.print("  kickoff [name]           # Full project pipeline: plan → setup → build → test → review → deliver")
        console.print("\n[bold cyan]Stages[/bold cyan]")
        console.print("  stage planning_discussion   # Active")
        console.print("  stages                      # List all stages")
        console.print("\n[bold cyan]File I/O[/bold cyan]")
        console.print("  @dev write code > file.py   |   @qa review < code.py")
        console.print()
    
    def print_team(self):
        table = Table(title="🤖 AI Team", box=box.ROUNDED)
        table.add_column("Role", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        
        team = [
            ("BA", Role.BA),
            ("QA", Role.QA),
            ("Senior Dev", Role.SENIOR_DEV),
            ("Coder", Role.CODER),
            ("Coder 2", Role.CODER_2),
            ("Reviewer", Role.REVIEWER),
        ]
        for role_name, role in team:
            provider, model = AgentFactory.get_role_runtime_config(role)
            table.add_row(role_name, model, provider.value)
        console.print()
        console.print(table)
        console.print()
    
    def print_workflows(self):
        table = Table(title="📋 Workflows", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Pipeline", style="green")
        
        workflows = [
            ("feature", "BA → QA → Senior → Coder → Coder2"),
            ("review", "Reviewer → Senior"),
            ("bugfix", "QA → Senior → Coder"),
            ("architecture", "BA → Senior → QA"),
            ("project_setup", "BA (creates issues) → Senior (architecture)"),
            ("pr_review", "Reviewer (reviews PR) → QA (test plan)"),
            ("full_feature", "BA → Senior → Coder → Coder2 → QA → Reviewer"),
            ("test_and_verify", "QA (test plan) → Coder (write tests) → QA (run tests)"),
        ]
        for name, pipeline in workflows:
            table.add_row(name, pipeline)
        console.print()
        console.print(table)
        console.print()

    def print_stages(self):
        table = Table(title="🧩 Stages", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description", style="white")

        catalog = self.orchestrator.get_stages()
        for stage_name in STAGES:
            if stage_name in catalog:
                details = catalog[stage_name]
                table.add_row(
                    stage_name,
                    details.get("status", "placeholder"),
                    details.get("description", ""),
                )

        for stage_name, details in catalog.items():
            if stage_name not in STAGES:
                table.add_row(
                    stage_name,
                    details.get("status", "placeholder"),
                    details.get("description", ""),
                )

        console.print()
        console.print(table)
        console.print()

    def _step_label(self, step_name: str) -> str:
        parts = step_name.split("_")
        if len(parts) <= 2:
            return step_name.upper()
        return "_".join(parts[2:]).upper()
    
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
        console.print("\n[bold blue]🤖 Team roundtable (BA first)...[/bold blue]\n")
        try:
            results = self.orchestrator.consult_team_discussion(prompt_text)
            for role, response in results.items():
                console.print(Panel(
                    Markdown(response.content),
                    title=f"[bold green]{role.value.upper()}[/bold green]",
                    subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
                    box=box.ROUNDED,
                ))
                console.print()
        except Exception as e:
            console.print(f"[red]Team discussion error: {e}[/red]")
    
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
                    role_name = self._step_label(step_name)
                    console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]", box=box.ROUNDED))
                    console.print()
            else:
                console.print("[red]✗ Workflow failed[/red]")
                for error in result.errors:
                    console.print(f"[red]  {error}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def handle_stage(self, args: list):
        if not args:
            console.print("[red]Usage: stage <name>[/red]")
            self.print_stages()
            return

        stage_name = args[0]
        if stage_name not in self.orchestrator.list_stages():
            console.print(f"[red]Unknown stage: {stage_name}[/red]")
            self.print_stages()
            return

        context = {}
        if stage_name == "planning_discussion":
            topic = Prompt.ask("[cyan]What should the team plan/discuss?[/cyan]")
            if not topic.strip():
                console.print("[red]A topic is required for planning_discussion[/red]")
                return
            context["requirement"] = topic

        console.print(f"\n[bold blue]🧩 Running stage: {stage_name}...[/bold blue]\n")
        try:
            result = self.orchestrator.run_stage(stage_name, context)
            if result.status.value == "completed":
                console.print(f"[green]✓ Done in {result.duration:.2f}s[/green]\n")
                for step_name, response in result.outputs.items():
                    role_name = self._step_label(step_name)
                    console.print(Panel(Markdown(response.content), title=f"[bold]{role_name}[/bold]", box=box.ROUNDED))
                    console.print()
            else:
                console.print("[red]✗ Stage failed[/red]")
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

            routing = Table(title="🧭 Effective Routing", box=box.ROUNDED)
            routing.add_column("Role", style="cyan")
            routing.add_column("Model", style="green")
            routing.add_column("Provider", style="blue")
            for role_name, role in [
                ("BA", Role.BA),
                ("QA", Role.QA),
                ("Senior Dev", Role.SENIOR_DEV),
                ("Coder", Role.CODER),
                ("Coder 2", Role.CODER_2),
                ("Reviewer", Role.REVIEWER),
            ]:
                provider, model = AgentFactory.get_role_runtime_config(role)
                routing.add_row(role_name, model, provider.value)
            console.print(routing)
            console.print()

            if settings.role_model_overrides or settings.role_provider_overrides:
                overrides = Table(title="⚙ Overrides", box=box.ROUNDED)
                overrides.add_column("Type", style="cyan")
                overrides.add_column("Value", style="white")
                overrides.add_row("role_model_overrides", str(settings.role_model_overrides))
                overrides.add_row("role_provider_overrides", str(settings.role_provider_overrides))
                console.print(overrides)
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

    def handle_github(self, args: list):
        """Show GitHub MCP integration status and available tools."""
        settings = get_settings()
        console.print()
        if not settings.github_mcp_enabled:
            console.print("[yellow]GitHub MCP is disabled.[/yellow]")
            console.print("  Set GITHUB_MCP_ENABLED=true and GITHUB_TOKEN in .env to enable.")
            console.print()
            return
        if not settings.github_token:
            console.print("[red]✗ GITHUB_TOKEN not set in .env[/red]")
            console.print()
            return

        # Connection status — trigger lazy init
        client = getattr(self.orchestrator, "_github_client", None)
        connected = client is not None and getattr(client, "_connected", False)
        if not connected and hasattr(self.orchestrator, "github_available"):
            # Attempt lazy connection with spinner
            with console.status("[bold blue]Connecting to GitHub MCP server...[/bold blue]"):
                try:
                    connected = self.orchestrator.github_available
                except Exception as e:
                    console.print(f"  [red]✗ Connection failed: {e}[/red]")
                    console.print()
                    return
            client = getattr(self.orchestrator, "_github_client", None)
        connected = client is not None and getattr(client, "_session", None) is not None
        status = "[green]Connected[/green]" if connected else "[red]Not connected[/red]"
        console.print(f"  GitHub MCP Status: {status}")
        console.print(f"  Command: {settings.github_mcp_command} {settings.github_mcp_args}")

        if connected:
            # Show per-role tool counts
            registries = getattr(self.orchestrator, "_github_registries", {})
            if registries:
                table = Table(title="GitHub Tools per Role", box=box.SIMPLE)
                table.add_column("Role", style="cyan")
                table.add_column("Tools", style="green", justify="right")
                for role_name, reg in sorted(registries.items()):
                    table.add_row(role_name, str(len(reg.list_tools())))
                console.print(table)

            # If subcommand: github tools <role>
            if args and args[0] == "tools" and len(args) > 1:
                role_name = args[1]
                reg = registries.get(role_name)
                if reg:
                    console.print(f"\n[bold]Tools for {role_name}:[/bold]")
                    for name in reg.list_tools():
                        defn = reg.get_definition(name)
                        desc = defn.description[:80] if defn and defn.description else ""
                        console.print(f"  [cyan]{name}[/cyan] — {desc}")
                else:
                    console.print(f"[yellow]No GitHub tools for role '{role_name}'[/yellow]")
        console.print()

    def handle_tools(self, args: list):
        """Show all tools available to each role."""
        from core.tool_registry import ToolRegistry
        console.print()
        roles = [
            ("BA", Role.BA),
            ("QA", Role.QA),
            ("Senior Dev", Role.SENIOR_DEV),
            ("Coder", Role.CODER),
            ("Coder 2", Role.CODER_2),
            ("Reviewer", Role.REVIEWER),
        ]

        # If a role filter was specified
        filter_role = args[0].lower() if args else None

        for role_name, role in roles:
            if filter_role and filter_role not in role_name.lower() and filter_role != role.value:
                continue
            registry = self.orchestrator._build_tool_registry(role)
            if registry and registry.list_tools():
                tool_names = registry.list_tools()
                console.print(f"[bold cyan]{role_name}[/bold cyan] ({len(tool_names)} tools)")
                for name in tool_names:
                    defn = registry.get_definition(name)
                    desc = (defn.description[:70] if defn and defn.description else "")
                    console.print(f"  [dim]•[/dim] {name} — {desc}")
                console.print()
            else:
                console.print(f"[bold cyan]{role_name}[/bold cyan] — [dim]no tools[/dim]")
        console.print()

    def handle_kickoff(self, args: list):
        """Run the full project pipeline — the flagship IT team experience."""
        project_name = args[0] if args else ""
        if not project_name:
            project_name = Prompt.ask("[cyan]Project name[/cyan]", default="my-project")

        requirement = Prompt.ask("[cyan]Describe the project (what should we build?)[/cyan]")
        if not requirement.strip():
            console.print("[red]A project description is required.[/red]")
            return

        repo_owner = ""
        skip_github = True
        settings = get_settings()
        if settings.github_mcp_enabled and settings.github_token:
            use_gh = Prompt.ask(
                "[cyan]Create GitHub repo?[/cyan]", choices=["yes", "no"], default="yes"
            )
            if use_gh == "yes":
                skip_github = False
                repo_owner = Prompt.ask("[cyan]GitHub owner (user/org)[/cyan]", default="")

        # ── phase status indicators ──────────────────────────────────
        phase_icons = {
            "planning": "📋", "setup": "🏗️", "build": "⚡",
            "quality": "🧪", "review": "🔍", "delivery": "📦",
        }
        phase_labels = {
            "planning": "Planning — BA stories, team discussion",
            "setup": "Setup — Architecture, project scaffolding",
            "build": "Build — Coders implement features",
            "quality": "Quality — QA tests & Excel test plan",
            "review": "Review — Code review & PR feedback",
            "delivery": "Delivery — Summary & run instructions",
        }
        step_count = 0
        phase_start_times: dict = {}

        def on_phase_start(phase_name: str):
            nonlocal step_count
            phase_start_times[phase_name] = time.time()
            icon = phase_icons.get(phase_name, "▶")
            label = phase_labels.get(phase_name, phase_name)
            console.print(f"\n{'─' * 60}")
            console.print(f"  {icon}  [bold blue]Phase: {label}[/bold blue]")
            console.print(f"{'─' * 60}")

        def on_step_done(phase_name: str, step_name: str, response):
            nonlocal step_count
            step_count += 1
            role_label = step_name.replace("_", " ").title()
            tokens = response.total_tokens
            console.print(f"\n  [green]✓[/green] {role_label} [dim]({response.model} | {tokens} tokens)[/dim]")

            # Show a truncated preview
            preview = response.content.strip()
            if len(preview) > 400:
                preview = preview[:400].rstrip() + "…"
            console.print(Panel(
                Markdown(preview),
                title=f"[bold]{role_label}[/bold]",
                subtitle=f"[dim]step {step_count}[/dim]",
                box=box.SIMPLE,
                width=min(console.width - 4, 100),
            ))

        def on_phase_done(result: PhaseResult):
            dur = result.duration
            icon = "✓" if result.status == PhaseStatus.COMPLETED else "✗"
            color = "green" if result.status == PhaseStatus.COMPLETED else "red"
            console.print(f"\n  [{color}]{icon} Phase {result.name} complete ({dur:.1f}s)[/{color}]")
            if result.errors:
                for err in result.errors:
                    console.print(f"    [red]Error: {err}[/red]")

        # ── run the pipeline ─────────────────────────────────────────
        console.print(f"\n[bold yellow]🚀 Kicking off project: {project_name}[/bold yellow]")
        console.print(f"[dim]Requirement: {requirement[:120]}{'…' if len(requirement) > 120 else ''}[/dim]")
        console.print(f"[dim]GitHub: {'enabled' if not skip_github else 'offline mode'}[/dim]\n")

        pipeline = ProjectPipeline(
            self.orchestrator,
            on_phase_start=on_phase_start,
            on_step_done=on_step_done,
            on_phase_done=on_phase_done,
        )

        t0 = time.time()
        result = pipeline.run(
            requirement=requirement,
            project_name=project_name,
            repo_owner=repo_owner,
            skip_github=skip_github,
        )
        total = time.time() - t0

        # ── final summary ────────────────────────────────────────────
        console.print(f"\n{'═' * 60}")
        if result.status == PhaseStatus.COMPLETED:
            console.print(f"[bold green]  ✓ PROJECT COMPLETE — {project_name}[/bold green]")
        else:
            console.print(f"[bold red]  ✗ PROJECT PIPELINE FAILED[/bold red]")
        console.print(f"  Total time: {total:.1f}s | Steps: {step_count}")
        console.print(f"{'═' * 60}")

        # Show delivery output in full
        delivery = result.phases.get("delivery")
        if delivery and delivery.outputs:
            last_output = list(delivery.outputs.values())[-1]
            console.print()
            console.print(Panel(
                Markdown(last_output.content),
                title="[bold green]📦 DELIVERY SUMMARY[/bold green]",
                box=box.DOUBLE,
            ))

        # Show artifacts summary
        artifacts = result.all_artifacts
        if artifacts:
            console.print("\n[bold cyan]Artifacts:[/bold cyan]")
            for key, val in artifacts.items():
                console.print(f"  {key}: {val}")

        console.print()

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
        elif cmd == "stages":
            self.print_stages()
        elif cmd == "config":
            self.handle_config()
        elif cmd == "clear":
            console.clear()
            self.print_banner()
        elif cmd == "workflow":
            self.handle_workflow(args)
        elif cmd == "stage":
            self.handle_stage(args)
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
        elif cmd == "github":
            self.handle_github(args)
        elif cmd == "tools":
            self.handle_tools(args)
        elif cmd == "kickoff":
            self.handle_kickoff(args)
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
