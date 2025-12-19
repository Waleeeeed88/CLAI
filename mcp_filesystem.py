"""
MCP Filesystem Tools for CLAI

Provides file system operations for AI agents to:
- Create and manage project repositories
- Read/write code files
- Search and navigate directories

All operations are sandboxed to MCP_WORKSPACE_ROOT.
"""
import os
import shutil
import fnmatch
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from config import get_settings


# ===========================================================================
# Data Classes
# ===========================================================================

@dataclass
class FileInfo:
    """Information about a file or directory."""
    path: str
    name: str
    is_dir: bool
    size: int = 0
    
    def __str__(self) -> str:
        prefix = "[DIR] " if self.is_dir else "[FILE]"
        size_str = f" ({self.size} bytes)" if not self.is_dir else ""
        return f"{prefix} {self.name}{size_str}"


@dataclass 
class OperationResult:
    """Result of a filesystem operation."""
    success: bool
    message: str
    data: Optional[str] = None


# ===========================================================================
# Filesystem Tools Class
# ===========================================================================

class FileSystemTools:
    """
    Sandboxed filesystem operations for AI agents.
    
    All paths are relative to the workspace root defined in settings.
    Prevents access outside the sandbox for security.
    
    Usage:
        fs = FileSystemTools()
        fs.create_project("my-app")
        fs.write_file("my-app/main.py", "print('hello')")
        content = fs.read_file("my-app/main.py")
    """
    
    def __init__(self):
        """Initialize with workspace root from settings."""
        settings = get_settings()
        self.workspace_root = settings.workspace_path
        self._ensure_workspace()
    
    def _ensure_workspace(self) -> None:
        """Ensure workspace directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to absolute, ensuring it's within sandbox.
        
        Args:
            relative_path: Path relative to workspace root
            
        Returns:
            Absolute Path object
            
        Raises:
            ValueError: If path escapes the sandbox
        """
        # Clean the path
        clean_path = relative_path.lstrip("/").lstrip("\\")
        
        # Resolve to absolute
        full_path = (self.workspace_root / clean_path).resolve()
        
        # Security check: ensure path is within workspace
        try:
            full_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"Path '{relative_path}' escapes workspace sandbox")
        
        return full_path
    
    # -----------------------------------------------------------------------
    # Project Operations
    # -----------------------------------------------------------------------
    
    def create_project(self, project_name: str, template: str = "basic") -> OperationResult:
        """
        Create a new project directory with optional template.
        
        Args:
            project_name: Name for the new project
            template: Template type ("basic", "python", "node", "empty")
            
        Returns:
            OperationResult with status
        """
        try:
            project_path = self._resolve_path(project_name)
            
            if project_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Project '{project_name}' already exists"
                )
            
            # Create project directory
            project_path.mkdir(parents=True)
            
            # Apply template
            if template == "python":
                self._apply_python_template(project_path, project_name)
            elif template == "node":
                self._apply_node_template(project_path, project_name)
            elif template == "basic":
                self._apply_basic_template(project_path, project_name)
            # "empty" creates just the directory
            
            return OperationResult(
                success=True,
                message=f"Created project '{project_name}' at {project_path}",
                data=str(project_path)
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def _apply_basic_template(self, path: Path, name: str) -> None:
        """Create basic project structure."""
        (path / "README.md").write_text(f"# {name}\n\nProject created by CLAI.\n")
        (path / ".gitignore").write_text("# Created by CLAI\n*.pyc\n__pycache__/\n.env\n")
    
    def _apply_python_template(self, path: Path, name: str) -> None:
        """Create Python project structure."""
        self._apply_basic_template(path, name)
        
        # Create src directory
        src_dir = path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text(f'"""{name} package."""\n')
        (src_dir / "main.py").write_text('"""Main entry point."""\n\n\ndef main():\n    print("Hello from CLAI!")\n\n\nif __name__ == "__main__":\n    main()\n')
        
        # Create tests directory
        tests_dir = path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_main.py").write_text('"""Tests for main module."""\n\n\ndef test_placeholder():\n    assert True\n')
        
        # Requirements
        (path / "requirements.txt").write_text("# Dependencies\n")
        
        # Update gitignore for Python
        gitignore = path / ".gitignore"
        gitignore.write_text(
            "# Python\n*.pyc\n__pycache__/\n*.egg-info/\ndist/\nbuild/\n.eggs/\n\n"
            "# Virtual env\nvenv/\n.venv/\nenv/\n\n"
            "# IDE\n.idea/\n.vscode/\n*.swp\n\n"
            "# Environment\n.env\n.env.local\n"
        )
    
    def _apply_node_template(self, path: Path, name: str) -> None:
        """Create Node.js project structure."""
        self._apply_basic_template(path, name)
        
        # package.json
        package_json = f'''{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "Created by CLAI",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "test": "echo \\"No tests yet\\""
  }}
}}
'''
        (path / "package.json").write_text(package_json)
        
        # Create src
        src_dir = path / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text('console.log("Hello from CLAI!");\n')
        
        # Update gitignore for Node
        gitignore = path / ".gitignore"
        gitignore.write_text(
            "# Node\nnode_modules/\n*.log\n\n"
            "# Build\ndist/\nbuild/\n\n"
            "# Environment\n.env\n.env.local\n"
        )
    
    def list_projects(self) -> List[str]:
        """List all projects in workspace."""
        projects = []
        for item in self.workspace_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                projects.append(item.name)
        return sorted(projects)
    
    def delete_project(self, project_name: str) -> OperationResult:
        """Delete a project and all its contents."""
        try:
            project_path = self._resolve_path(project_name)
            
            if not project_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Project '{project_name}' not found"
                )
            
            if not project_path.is_dir():
                return OperationResult(
                    success=False,
                    message=f"'{project_name}' is not a project directory"
                )
            
            shutil.rmtree(project_path)
            return OperationResult(
                success=True,
                message=f"Deleted project '{project_name}'"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    # -----------------------------------------------------------------------
    # File Operations
    # -----------------------------------------------------------------------
    
    def read_file(self, file_path: str) -> OperationResult:
        """
        Read contents of a file.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            OperationResult with file contents in data field
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return OperationResult(
                    success=False,
                    message=f"File not found: {file_path}"
                )
            
            if not full_path.is_file():
                return OperationResult(
                    success=False,
                    message=f"Not a file: {file_path}"
                )
            
            content = full_path.read_text(encoding="utf-8")
            return OperationResult(
                success=True,
                message=f"Read {len(content)} bytes from {file_path}",
                data=content
            )
            
        except UnicodeDecodeError:
            return OperationResult(
                success=False,
                message=f"Cannot read binary file: {file_path}"
            )
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def write_file(self, file_path: str, content: str) -> OperationResult:
        """
        Write content to a file, creating directories as needed.
        
        Args:
            file_path: Relative path to file
            content: Content to write
            
        Returns:
            OperationResult with status
        """
        try:
            full_path = self._resolve_path(file_path)
            
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content, encoding="utf-8")
            
            return OperationResult(
                success=True,
                message=f"Wrote {len(content)} bytes to {file_path}",
                data=str(full_path)
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def append_file(self, file_path: str, content: str) -> OperationResult:
        """Append content to a file."""
        try:
            full_path = self._resolve_path(file_path)
            
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(content)
            
            return OperationResult(
                success=True,
                message=f"Appended {len(content)} bytes to {file_path}"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def delete_file(self, file_path: str) -> OperationResult:
        """Delete a file."""
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return OperationResult(
                    success=False,
                    message=f"File not found: {file_path}"
                )
            
            if full_path.is_dir():
                return OperationResult(
                    success=False,
                    message=f"Use delete_project for directories: {file_path}"
                )
            
            full_path.unlink()
            return OperationResult(
                success=True,
                message=f"Deleted {file_path}"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    # -----------------------------------------------------------------------
    # Directory Operations
    # -----------------------------------------------------------------------
    
    def list_directory(self, dir_path: str = ".") -> List[FileInfo]:
        """
        List contents of a directory.
        
        Args:
            dir_path: Relative path to directory (default: workspace root)
            
        Returns:
            List of FileInfo objects
        """
        try:
            full_path = self._resolve_path(dir_path)
            
            if not full_path.exists():
                return []
            
            if not full_path.is_dir():
                return []
            
            items = []
            for item in sorted(full_path.iterdir()):
                info = FileInfo(
                    path=str(item.relative_to(self.workspace_root)),
                    name=item.name,
                    is_dir=item.is_dir(),
                    size=item.stat().st_size if item.is_file() else 0
                )
                items.append(info)
            
            return items
            
        except Exception:
            return []
    
    def create_directory(self, dir_path: str) -> OperationResult:
        """Create a directory (and parents if needed)."""
        try:
            full_path = self._resolve_path(dir_path)
            full_path.mkdir(parents=True, exist_ok=True)
            
            return OperationResult(
                success=True,
                message=f"Created directory: {dir_path}"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def get_tree(self, dir_path: str = ".", max_depth: int = 3) -> str:
        """
        Get a tree view of directory structure.
        
        Args:
            dir_path: Starting directory
            max_depth: Maximum depth to traverse
            
        Returns:
            String representation of directory tree
        """
        try:
            full_path = self._resolve_path(dir_path)
            
            if not full_path.exists() or not full_path.is_dir():
                return f"Directory not found: {dir_path}"
            
            lines = [full_path.name + "/"]
            self._build_tree(full_path, "", lines, max_depth, 0)
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error: {e}"
    
    def _build_tree(
        self, 
        path: Path, 
        prefix: str, 
        lines: List[str], 
        max_depth: int, 
        current_depth: int
    ) -> None:
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            return
        
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._build_tree(item, new_prefix, lines, max_depth, current_depth + 1)
            else:
                lines.append(f"{prefix}{connector}{item.name}")
    
    # -----------------------------------------------------------------------
    # Search Operations
    # -----------------------------------------------------------------------
    
    def search_files(
        self, 
        pattern: str, 
        dir_path: str = ".",
        include_content: bool = False
    ) -> List[str]:
        """
        Search for files matching a pattern.
        
        Args:
            pattern: Glob pattern (e.g., "*.py", "test_*.py")
            dir_path: Directory to search in
            include_content: If True, search in file contents too
            
        Returns:
            List of matching file paths
        """
        try:
            full_path = self._resolve_path(dir_path)
            matches = []
            
            for root, dirs, files in os.walk(full_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        file_path = Path(root) / filename
                        rel_path = str(file_path.relative_to(self.workspace_root))
                        matches.append(rel_path)
            
            return sorted(matches)
            
        except Exception:
            return []
    
    def grep(self, search_term: str, dir_path: str = ".", file_pattern: str = "*") -> List[str]:
        """
        Search for text in files.
        
        Args:
            search_term: Text to search for
            dir_path: Directory to search in
            file_pattern: Only search in files matching this pattern
            
        Returns:
            List of "file:line:content" matches
        """
        try:
            full_path = self._resolve_path(dir_path)
            matches = []
            
            for root, dirs, files in os.walk(full_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                
                for filename in files:
                    if not fnmatch.fnmatch(filename, file_pattern):
                        continue
                    
                    file_path = Path(root) / filename
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            for line_num, line in enumerate(f, 1):
                                if search_term.lower() in line.lower():
                                    rel_path = str(file_path.relative_to(self.workspace_root))
                                    matches.append(f"{rel_path}:{line_num}:{line.strip()}")
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            return matches
            
        except Exception:
            return []


# ===========================================================================
# Singleton Instance
# ===========================================================================

_fs_instance: Optional[FileSystemTools] = None


def get_filesystem() -> FileSystemTools:
    """Get singleton filesystem instance."""
    global _fs_instance
    if _fs_instance is None:
        _fs_instance = FileSystemTools()
    return _fs_instance
