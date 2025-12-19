"""
CLAI Interactive Shell
======================

The main UI for talking to your AI team. Launch with: python shell.py

Features:
  - @mentions: @senior, @dev, @qa, @ba, @reviewer, @team
  - File I/O:  @dev write X > file.py  |  @qa review < code.py
  - Workflows: workflow feature, workflow review, etc.
  - Tab completion & command history

Example session:
    clai> @senior design a REST API
    clai> @dev implement that > api.py
    clai> @qa check for bugs < api.py
"""

# ===========================================================================
# Imports
# ===========================================================================

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich import box
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
import os
import sys
import re
from pathlib import Path
from typing import Optional, Dict

# Make sure we can import from project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.factory import Role
from orchestrator import Orchestrator
from config import get_settings
from mcp_filesystem import get_filesystem, FileSystemTools

# Rich console for pretty output
console = Console()


# ===========================================================================
# Configuration: Commands, Roles, and @Mentions
# ===========================================================================

# Shell commands the user can type
COMMANDS = [
    "help", "team", "workflows", "workflow", "config",
    "clear", "history", "save", "exit", "quit",
    # Filesystem commands
    "projects", "newproject", "files", "tree", "readfile", "workspace"
]

# Available team roles
ROLES = ["senior_dev", "coder", "coder_2", "qa", "ba", "reviewer"]

# Multi-agent workflows
WORKFLOWS = ["feature", "review", "bugfix", "architecture"]

# @mention aliases — multiple ways to call each team member
MENTION_ALIASES: Dict[str, Role] = {
    # Senior Developer (Claude) - architecture, complex problems
    "@senior":     Role.SENIOR_DEV,
    "@seniordev":  Role.SENIOR_DEV,
    "@architect":  Role.SENIOR_DEV,
    "@lead":       Role.SENIOR_DEV,
    "@tech":       Role.SENIOR_DEV,
    
    # Coder (Claude) - fast implementation
    "@dev":        Role.CODER,
    "@coder":      Role.CODER,
    "@dev1":       Role.CODER,
    "@developer":  Role.CODER,
    "@code":       Role.CODER,
    
    # Coder 2 (Gemini) - secondary coder, large context
    "@dev2":       Role.CODER_2,
    "@coder2":     Role.CODER_2,
    "@gemini":     Role.CODER_2,
    
    # QA Engineer (GPT) - testing, bugs
    "@qa":         Role.QA,
    "@test":       Role.QA,
    "@tester":     Role.QA,
    "@quality":    Role.QA,
    "@bug":        Role.QA,
    
    # Business Analyst (Gemini) - requirements, specs
    "@ba":         Role.BA,
    "@analyst":    Role.BA,
    "@specs":      Role.BA,
    "@reqs":       Role.BA,
    
    # Code Reviewer (Claude) - quick reviews
    "@reviewer":   Role.REVIEWER,
    "@review":     Role.REVIEWER,
    "@cr":         Role.REVIEWER,
}

# These @mentions ask ALL team members
TEAM_MENTIONS = ["@team", "@all", "@devteam", "@everyone"]


# ===========================================================================
# Tab Completion for @mentions
# ===========================================================================

class MentionCompleter(Completer):
    """Autocomplete @mentions and commands as you type."""
    
    def __init__(self):
        self.mentions = list(MENTION_ALIASES.keys()) + TEAM_MENTIONS
        self.commands = COMMANDS + WORKFLOWS
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()
        
        # Completing an @mention?
        if "@" in text:
            at_pos = text.rfind("@")
            partial = text[at_pos:].lower()
            
            for mention in self.mentions:
                if mention.startswith(partial):
                    yield Completion(
                        mention,
                        start_position=-len(partial),
                        style="fg:cyan bold",
                    )
        else:
            # Regular command completion
            for cmd in self.commands:
                if cmd.startswith(word.lower()):
                    yield Completion(cmd, start_position=-len(word))


# ===========================================================================
# The Main Shell Class
# ===========================================================================

class CLAIShell:
    """
    The interactive CLAI shell.
    
    This is where the magic happens. It:
    - Shows a prompt and waits for input
    - Parses @mentions and routes to the right AI
    - Handles file input/output (< and >)
    - Runs multi-agent workflows
    """
    
    def __init__(self):
        # The orchestrator manages all our AI agents
        self.orchestrator = Orchestrator(verbose=False)
        
        # Filesystem tools for project management
        self.fs = get_filesystem()
        
        # Track state
        self.current_role: Optional[Role] = None  # For chat mode
        self.running = True
        self.last_response = None  # For 'save' command
        
        # Paths
        self.history_file = Path.home() / ".clai_history"
        self.output_dir = Path.cwd() / "clai_output"
        
        # Tab completion
        self.completer = MentionCompleter()
    
    # -----------------------------------------------------------------------
    # UI: Banner and Help
    # -----------------------------------------------------------------------
    
    def print_banner(self):
        """Show the welcome screen."""
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗██╗      █████╗ ██╗                                      ║
║  ██╔════╝██║     ██╔══██╗██║                                      ║
║  ██║     ██║     ███████║██║                                      ║
║  ██║     ██║     ██╔══██║██║                                      ║
║  ╚██████╗███████╗██║  ██║██║                                      ║
║   ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝                                      ║
║                                                                   ║
║   🤖 Command Line AI Team                                         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
        console.print(banner, style="bold blue")
    
    def print_help(self):
        """Show help with examples."""
        
        # @mentions
        console.print("\n[bold cyan]📣 @Mentions — Talk to Your Team[/bold cyan]")
        mention_table = Table(box=box.SIMPLE)
        mention_table.add_column("Who", style="cyan bold")
        mention_table.add_column("Also responds to", style="dim")
        mention_table.add_column("Example", style="green")
        
        mention_table.add_row("@senior", "@architect @lead @tech", "@senior design a REST API")
        mention_table.add_row("@dev", "@coder @developer @code", "@dev implement binary search")
        mention_table.add_row("@qa", "@test @tester @bug", "@qa review this for bugs")
        mention_table.add_row("@ba", "@analyst @specs @reqs", "@ba write user stories")
        mention_table.add_row("@reviewer", "@review @cr", "@reviewer check code style")
        mention_table.add_row("@team", "@all @everyone", "@team thoughts on this?")
        console.print(mention_table)
        
        # File I/O
        console.print("\n[bold cyan]📁 File Operations[/bold cyan]")
        file_table = Table(box=box.SIMPLE)
        file_table.add_column("Syntax", style="cyan")
        file_table.add_column("What it does", style="white")
        
        file_table.add_row("@dev write X > file.py", "Save AI output to file")
        file_table.add_row("@qa review < code.py", "Load file as context")
        file_table.add_row("@senior look at < src/", "Load whole directory")
        file_table.add_row("save filename.md", "Save last response")
        console.print(file_table)
        
        # Commands
        console.print("\n[bold cyan]⌨️  Commands[/bold cyan]")
        cmd_table = Table(box=box.SIMPLE)
        cmd_table.add_column("Command", style="cyan")
        cmd_table.add_column("What it does", style="white")
        
        commands = [
            ("team", "Show AI team status"),
            ("workflows", "List multi-agent pipelines"),
            ("workflow <name>", "Run: feature, review, bugfix, architecture"),
            ("config", "Check API keys"),
            ("clear", "Clear screen"),
            ("history", "Show conversation history"),
            ("exit", "Quit CLAI"),
        ]
        for cmd, desc in commands:
            cmd_table.add_row(cmd, desc)
        console.print(cmd_table)
        
        # Project/Filesystem Commands
        console.print("\n[bold cyan]📂 Project Commands[/bold cyan]")
        proj_table = Table(box=box.SIMPLE)
        proj_table.add_column("Command", style="cyan")
        proj_table.add_column("What it does", style="white")
        
        proj_commands = [
            ("projects", "List all projects in workspace"),
            ("newproject <name>", "Create new project (python/node/basic)"),
            ("files [path]", "List files in directory"),
            ("tree [path]", "Show directory tree"),
            ("readfile <path>", "View file contents"),
            ("workspace", "Show workspace root path"),
        ]
        for cmd, desc in proj_commands:
            proj_table.add_row(cmd, desc)
        console.print(proj_table)
        console.print()
    
    def print_team(self):
        """Show team status."""
        settings = get_settings()
        
        table = Table(title="🤖 AI Team", box=box.ROUNDED)
        table.add_column("Role", style="cyan", no_wrap=True)
        table.add_column("Model", style="green")
        table.add_column("Provider", style="blue")
        table.add_column("Status")
        
        team = [
            ("Senior Dev", settings.senior_dev_model, "Anthropic"),
            ("Coder", settings.coder_model, "Anthropic"),
            ("Coder 2", settings.coder_model_2, "Google"),
            ("QA", settings.qa_model, "OpenAI"),
            ("BA", settings.ba_model, "Google"),
            ("Reviewer", settings.reviewer_model, "Anthropic"),
        ]
        
        for role, model, provider in team:
            table.add_row(role, model, provider, "[green]● Ready[/green]")
        
        console.print()
        console.print(table)
        console.print()
    
    def print_workflows(self):
        """Show available multi-agent workflows."""
        table = Table(title="📋 Workflows", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Pipeline", style="green")
        table.add_column("Use For", style="white")
        
        workflows = [
            ("feature", "BA → Senior → Coder → QA", "New features end-to-end"),
            ("review", "Reviewer → Senior", "Code review + improvements"),
            ("bugfix", "QA → Senior → Coder", "Analyze & fix bugs"),
            ("architecture", "BA → Senior → QA", "System design"),
        ]
        
        for name, pipeline, use in workflows:
            table.add_row(name, pipeline, use)
        
        console.print()
        console.print(table)
        console.print()
    
    # -----------------------------------------------------------------------
    # Core: Talking to AI Agents
    # -----------------------------------------------------------------------
    
    def handle_ask(self, args: list):
        """Handle the 'ask' command (legacy, prefer @mentions)."""
        if len(args) < 2:
            console.print("[red]Usage: ask <role> <prompt>[/red]")
            return
        
        role_name = args[0]
        prompt_text = " ".join(args[1:])
        
        if role_name not in ROLES:
            console.print(f"[red]Unknown role: {role_name}[/red]")
            console.print(f"[yellow]Available: {', '.join(ROLES)}[/yellow]")
            return
        
        self._query_agent(Role(role_name), prompt_text)
    
    def _query_agent(self, role: Role, prompt_text: str, save_to: Optional[str] = None):
        """
        Send a message to one AI agent and display the response.
        
        Args:
            role: Which team member to ask (SENIOR_DEV, CODER, etc.)
            prompt_text: What to ask them
            save_to: Optional filename to save the response
        """
        role_name = role.value
        
        with console.status(f"[bold blue]{role_name} is thinking...[/bold blue]"):
            try:
                response = self.orchestrator.ask(role, prompt_text)
                self.last_response = response
                
                # Show the response in a nice panel
                console.print()
                console.print(Panel(
                    Markdown(response.content),
                    title=f"[bold green]{role_name.upper()}[/bold green]",
                    subtitle=f"[dim]{response.model} | {response.total_tokens} tokens[/dim]",
                    box=box.ROUNDED,
                ))
                console.print()
                
                # Save if requested
                if save_to:
                    self._save_to_file(response.content, save_to)
                    
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    def _query_team(self, prompt_text: str):
        """Ask ALL team members the same question (for @team mentions)."""
        console.print("\n[bold blue]🤖 Asking the whole team...[/bold blue]\n")
        
        for role in [Role.SENIOR_DEV, Role.CODER, Role.QA, Role.BA]:
            with console.status(f"[bold blue]{role.value} is thinking...[/bold blue]"):
                try:
                    response = self.orchestrator.ask(role, prompt_text)
                    
                    console.print(Panel(
                        Markdown(response.content),
                        title=f"[bold green]{role.value.upper()}[/bold green]",
                        subtitle=f"[dim]{response.model}[/dim]",
                        box=box.ROUNDED,
                    ))
                    console.print()
                except Exception as e:
                    console.print(f"[red]{role.value} error: {str(e)}[/red]")
    
    # -----------------------------------------------------------------------
    # File I/O: Save responses, load files as context
    # -----------------------------------------------------------------------
    
    def _save_to_file(self, content: str, filename: str):
        """
        Save AI response to a file.
        
        Smart behavior:
        - For code files (.py, .js, etc.), extracts just the code block
        - For other files, saves the full markdown response
        """
        try:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # For code files, try to extract just the code block
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
        """
        Load a file or directory to include as context in the prompt.
        
        Returns formatted string with file contents wrapped in code blocks.
        """
        path = Path(filepath)
        
        if not path.exists():
            console.print(f"[red]Not found: {filepath}[/red]")
            return ""
        
        # Single file
        if path.is_file():
            content = path.read_text()
            return f"\n\n---\nFile: {path.name}\n```\n{content}\n```\n"
        
        # Directory - load all code files
        if path.is_dir():
            context = f"\n\n---\nDirectory: {path}\n"
            code_extensions = {
                ".py", ".js", ".ts", ".java", ".cpp", ".c", 
                ".go", ".rs", ".md", ".txt", ".json", ".yaml", ".yml"
            }
            
            for file in path.rglob("*"):
                if file.is_file() and file.suffix in code_extensions:
                    try:
                        content = file.read_text()
                        rel_path = file.relative_to(path)
                        context += f"\n### {rel_path}\n```\n{content}\n```\n"
                    except:
                        pass  # Skip files we can't read
            
            return context
        
        return ""
    
    # -----------------------------------------------------------------------
    # @Mention Parsing: The core of the natural command syntax
    # -----------------------------------------------------------------------
    
    def handle_mention(self, user_input: str):
        """
        Parse and handle @mention commands.
        
        Supports:
            @senior do something          -> Ask senior dev
            @dev write code > file.py     -> Save output to file
            @qa review < code.py          -> Load file as context
            @team what do you think?      -> Ask everyone
        """
        
        # Step 1: Check for output redirect (> filename)
        save_to = None
        if ">" in user_input:
            parts = user_input.split(">")
            user_input = parts[0].strip()
            save_to = parts[1].strip()
        
        # Step 2: Check for input file (< filename)
        file_context = ""
        if "<" in user_input:
            parts = user_input.split("<")
            user_input = parts[0].strip()
            file_path = parts[1].strip()
            file_context = self._load_file_context(file_path)
        
        # Step 3: Find @mentions and extract the target role
        mentions_found = []
        for mention, role in MENTION_ALIASES.items():
            if mention in user_input.lower():
                mentions_found.append((mention, role))
                # Remove the mention from the prompt
                user_input = re.sub(re.escape(mention), "", user_input, flags=re.IGNORECASE)
        
        # Step 4: Check for @team/@all mentions
        is_team_query = any(tm in user_input.lower() for tm in TEAM_MENTIONS)
        if is_team_query:
            for tm in TEAM_MENTIONS:
                user_input = re.sub(re.escape(tm), "", user_input, flags=re.IGNORECASE)
        
        # Step 5: Build final prompt
        prompt_text = user_input.strip() + file_context
        
        if not prompt_text.strip():
            console.print("[yellow]What would you like to ask?[/yellow]")
            return
        
        # Step 6: Route to the right handler
        if is_team_query:
            self._query_team(prompt_text)
        elif mentions_found:
            _, role = mentions_found[0]  # Use first @mention found
            self._query_agent(role, prompt_text, save_to)
        else:
            console.print("[yellow]No @mention found. Try: @senior, @dev, @qa, @ba, @team[/yellow]")
    
    # -----------------------------------------------------------------------
    # Workflows: Multi-agent pipelines
    # -----------------------------------------------------------------------
    
    def handle_workflow(self, args: list):
        """
        Run a multi-agent workflow.
        
        Workflows:
            feature      -> BA → Senior → Coder → QA
            review       -> Reviewer → Senior
            bugfix       -> QA → Senior → Coder  
            architecture -> BA → Senior → QA
        """
        if not args:
            console.print("[red]Usage: workflow <name>[/red]")
            self.print_workflows()
            return
        
        workflow_name = args[0]
        if workflow_name not in WORKFLOWS:
            console.print(f"[red]Unknown workflow: {workflow_name}[/red]")
            return
        
        # Gather required input based on workflow type
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
        
        # Run it
        console.print(f"\n[bold blue]🚀 Running {workflow_name} workflow...[/bold blue]\n")
        
        try:
            result = self.orchestrator.run_workflow(workflow_name, context)
            
            if result.status.value == "completed":
                console.print(f"[green]✓ Done in {result.duration:.2f}s[/green]\n")
                
                for step_name, response in result.outputs.items():
                    role_name = step_name.split("_")[-1].upper()
                    console.print(Panel(
                        Markdown(response.content),
                        title=f"[bold]{role_name}[/bold]",
                        subtitle=f"[dim]{response.model}[/dim]",
                        box=box.ROUNDED,
                    ))
                    console.print()
            else:
                console.print("[red]✗ Workflow failed[/red]")
                for error in result.errors:
                    console.print(f"[red]  {error}[/red]")
                    
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    # -----------------------------------------------------------------------
    # Other Commands
    # -----------------------------------------------------------------------
    
    def handle_switch(self, args: list):
        """Switch to chat mode with one role (legacy, prefer @mentions)."""
        if not args:
            if self.current_role:
                console.print(f"[yellow]Chatting with: {self.current_role.value}[/yellow]")
            else:
                console.print("[yellow]Not in chat mode. Use: switch <role>[/yellow]")
            return
        
        role_name = args[0]
        if role_name not in ROLES:
            console.print(f"[red]Unknown role: {role_name}[/red]")
            return
        
        self.current_role = Role(role_name)
        console.print(f"[green]Now chatting with {role_name}. Type 'switch' to exit.[/green]")
    
    def handle_config(self):
        """Show API key status."""
        try:
            settings = get_settings()
            
            table = Table(title="🔑 API Keys", box=box.ROUNDED)
            table.add_column("Provider", style="cyan")
            table.add_column("Status")
            
            keys = [
                ("Anthropic", bool(settings.anthropic_api_key.get_secret_value())),
                ("OpenAI", bool(settings.openai_api_key.get_secret_value())),
                ("Google", bool(settings.google_api_key.get_secret_value())),
            ]
            
            for provider, ok in keys:
                status = "[green]✓ Set[/green]" if ok else "[red]✗ Missing[/red]"
                table.add_row(provider, status)
            
            console.print()
            console.print(table)
            console.print()
            
        except Exception as e:
            console.print(f"[red]Config error: {str(e)}[/red]")
            console.print("[yellow]Make sure .env file exists with API keys[/yellow]")
    
    # -----------------------------------------------------------------------
    # Filesystem Commands: Create and manage project repos
    # -----------------------------------------------------------------------
    
    def handle_projects(self):
        """List all projects in the workspace."""
        projects = self.fs.list_projects()
        
        if not projects:
            console.print("\n[yellow]No projects yet. Create one with: newproject <name>[/yellow]")
            console.print(f"[dim]Workspace: {self.fs.workspace_root}[/dim]\n")
            return
        
        table = Table(title="📂 Projects", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Files", style="green")
        
        for project in projects:
            files = self.fs.list_directory(project)
            file_count = len([f for f in files if not f.is_dir])
            table.add_row(project, str(file_count))
        
        console.print()
        console.print(table)
        console.print(f"\n[dim]Workspace: {self.fs.workspace_root}[/dim]\n")
    
    def handle_new_project(self, args: list):
        """Create a new project."""
        if not args:
            console.print("[yellow]Usage: newproject <name> [python|node|basic][/yellow]")
            return
        
        name = args[0]
        template = args[1] if len(args) > 1 else "python"
        
        result = self.fs.create_project(name, template)
        
        if result.success:
            console.print(f"\n[green]✓ {result.message}[/green]")
            console.print(f"\n[cyan]Project structure:[/cyan]")
            tree = self.fs.get_tree(name)
            console.print(tree)
            console.print()
        else:
            console.print(f"[red]✗ {result.message}[/red]")
    
    def handle_files(self, args: list):
        """List files in a directory."""
        path = args[0] if args else "."
        files = self.fs.list_directory(path)
        
        if not files:
            console.print(f"[yellow]Directory empty or not found: {path}[/yellow]")
            return
        
        console.print(f"\n[cyan]📁 {path}[/cyan]\n")
        for f in files:
            if f.is_dir:
                console.print(f"  [blue]📁 {f.name}/[/blue]")
            else:
                console.print(f"  [white]📄 {f.name}[/white] [dim]({f.size} bytes)[/dim]")
        console.print()
    
    def handle_tree(self, args: list):
        """Show directory tree."""
        path = args[0] if args else "."
        depth = int(args[1]) if len(args) > 1 else 3
        
        tree = self.fs.get_tree(path, max_depth=depth)
        console.print(f"\n[cyan]{tree}[/cyan]\n")
    
    def handle_read_file(self, args: list):
        """Read and display a file."""
        if not args:
            console.print("[yellow]Usage: readfile <path>[/yellow]")
            return
        
        result = self.fs.read_file(args[0])
        
        if result.success:
            # Determine syntax highlighting based on extension
            ext = Path(args[0]).suffix.lstrip(".")
            syntax_map = {
                "py": "python", "js": "javascript", "ts": "typescript",
                "json": "json", "md": "markdown", "yaml": "yaml", "yml": "yaml",
                "html": "html", "css": "css", "sh": "bash"
            }
            syntax = syntax_map.get(ext, "")
            
            console.print(f"\n[cyan]📄 {args[0]}[/cyan]\n")
            if syntax:
                from rich.syntax import Syntax
                console.print(Syntax(result.data, syntax, theme="monokai", line_numbers=True))
            else:
                console.print(result.data)
            console.print()
        else:
            console.print(f"[red]✗ {result.message}[/red]")
    
    def get_prompt_text(self) -> str:
        """Get the prompt text based on current state."""
        if self.current_role:
            return f"clai ({self.current_role.value})> "
        return "clai> "
    
    def process_input(self, user_input: str):
        """Process user input."""
        user_input = user_input.strip()
        if not user_input:
            return
        
        # Parse command and arguments
        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        # ---------------------
        # Chat mode: direct messages go to current role
        # ---------------------
        if self.current_role and cmd not in COMMANDS:
            self.handle_ask([self.current_role.value, user_input])
            return
        
        # ---------------------
        # Command dispatch
        # ---------------------
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
            
        elif cmd == "ask":
            self.handle_ask(args)
            
        elif cmd == "switch":
            if not args:
                self.current_role = None
                console.print("[yellow]Exited chat mode[/yellow]")
            else:
                self.handle_switch(args)
                
        elif cmd == "chat":
            self.handle_switch(args)
            
        elif cmd == "workflow":
            self.handle_workflow(args)
            
        elif cmd == "history":
            # Show message count per agent
            for role, agent in self.orchestrator._agents.items():
                if agent.conversation_history:
                    console.print(f"\n[bold]{role.value}[/bold]: {len(agent.conversation_history)} messages")
        
        elif cmd == "save":
            # Save last response to file
            if hasattr(self, "last_response") and self.last_response:
                if args:
                    self._save_to_file(self.last_response.content, args[0])
                else:
                    console.print("[yellow]Usage: save <filename>[/yellow]")
            else:
                console.print("[yellow]No response to save yet[/yellow]")
        
        # ---------------------
        # Filesystem Commands
        # ---------------------
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
        
        # ---------------------
        # @mention handling
        # ---------------------
        elif user_input.startswith("@"):
            self.handle_mention(user_input)
                    
        else:
            # Maybe @mention is somewhere in the text
            if "@" in user_input:
                self.handle_mention(user_input)
            else:
                console.print("[yellow]Tip: Use @mentions like @senior, @dev, @qa, @ba, @team[/yellow]")
                console.print("[yellow]Example: @dev write a hello world in python[/yellow]")
    
    # -----------------------------------------------------------------------
    # Main Loop
    # -----------------------------------------------------------------------
    
    def run(self):
        """
        Start the interactive shell.
        
        Flow:
            1. Clear screen, show banner and help
            2. Validate config (API keys)
            3. Enter input loop with tab-completion and history
            4. Handle Ctrl+C gracefully
        """
        console.clear()
        self.print_banner()
        self.print_help()
        
        # Check API configuration
        try:
            get_settings()
            console.print("[green]✓ Configuration loaded[/green]\n")
        except Exception as e:
            console.print(f"[red]⚠ Config error: {e}[/red]")
            console.print("[yellow]Run 'config' for details[/yellow]\n")
        
        # Main input loop
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


# ===========================================================================
# Entry Point
# ===========================================================================

def main():
    """Entry point for the interactive shell."""
    shell = CLAIShell()
    shell.run()


if __name__ == "__main__":
    main()
