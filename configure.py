#!/usr/bin/env python3
"""
CLAI - Command Line AI Team

Main entry point for the CLI application.
Run with: python configure.py [command]
Or:       python configure.py shell (for interactive UI)
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli import main, cli

# Add shell command to CLI
@cli.command()
def shell():
    """Launch the interactive CLAI shell UI."""
    from shell import main as shell_main
    shell_main()

if __name__ == '__main__':
    main()