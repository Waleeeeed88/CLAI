"""Sandboxed filesystem operations."""
import os
import shutil
import fnmatch
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from config import get_settings


@dataclass
class FileInfo:
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
    success: bool
    message: str
    data: Optional[str] = None


class FileSystemTools:
    def __init__(self):
        settings = get_settings()
        self.workspace_root = settings.workspace_path
        self._ensure_workspace()
    
    def _ensure_workspace(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, relative_path: str) -> Path:
        clean_path = relative_path.lstrip("/").lstrip("\\")
        full_path = (self.workspace_root / clean_path).resolve()
        try:
            full_path.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"Path '{relative_path}' escapes workspace sandbox")
        return full_path
    
    def create_project(self, project_name: str, template: str = "basic") -> OperationResult:
        try:
            project_path = self._resolve_path(project_name)
            if project_path.exists():
                return OperationResult(False, f"Project '{project_name}' already exists")
            
            project_path.mkdir(parents=True)
            
            if template == "python":
                self._apply_python_template(project_path, project_name)
            elif template == "node":
                self._apply_node_template(project_path, project_name)
            elif template == "basic":
                self._apply_basic_template(project_path, project_name)
            
            return OperationResult(True, f"Created project '{project_name}'", str(project_path))
        except Exception as e:
            return OperationResult(False, str(e))
    
    def _apply_basic_template(self, path: Path, name: str) -> None:
        (path / "README.md").write_text(f"# {name}\n\nProject created by CLAI.\n")
        (path / ".gitignore").write_text("*.pyc\n__pycache__/\n.env\n")
    
    def _apply_python_template(self, path: Path, name: str) -> None:
        self._apply_basic_template(path, name)
        src_dir = path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text(f'"""{name} package."""\n')
        (src_dir / "main.py").write_text('def main():\n    print("Hello from CLAI!")\n\nif __name__ == "__main__":\n    main()\n')
        tests_dir = path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_main.py").write_text("def test_placeholder():\n    assert True\n")
        (path / "requirements.txt").write_text("")
        (path / ".gitignore").write_text("*.pyc\n__pycache__/\nvenv/\n.venv/\n.env\n")
    
    def _apply_node_template(self, path: Path, name: str) -> None:
        self._apply_basic_template(path, name)
        package_json = f'{{\n  "name": "{name}",\n  "version": "1.0.0",\n  "main": "src/index.js"\n}}\n'
        (path / "package.json").write_text(package_json)
        src_dir = path / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text('console.log("Hello from CLAI!");\n')
        (path / ".gitignore").write_text("node_modules/\n.env\n")
    
    def list_projects(self) -> List[str]:
        return sorted([d.name for d in self.workspace_root.iterdir() if d.is_dir() and not d.name.startswith(".")])
    
    def delete_project(self, project_name: str) -> OperationResult:
        try:
            project_path = self._resolve_path(project_name)
            if not project_path.exists():
                return OperationResult(False, f"Project '{project_name}' not found")
            if not project_path.is_dir():
                return OperationResult(False, f"'{project_name}' is not a directory")
            shutil.rmtree(project_path)
            return OperationResult(True, f"Deleted project '{project_name}'")
        except Exception as e:
            return OperationResult(False, str(e))
    
    def read_file(self, file_path: str) -> OperationResult:
        try:
            full_path = self._resolve_path(file_path)
            if not full_path.exists():
                return OperationResult(False, f"File not found: {file_path}")
            if not full_path.is_file():
                return OperationResult(False, f"Not a file: {file_path}")
            content = full_path.read_text(encoding="utf-8")
            return OperationResult(True, f"Read {len(content)} bytes", content)
        except UnicodeDecodeError:
            return OperationResult(False, f"Cannot read binary file: {file_path}")
        except Exception as e:
            return OperationResult(False, str(e))
    
    def write_file(self, file_path: str, content: str) -> OperationResult:
        try:
            full_path = self._resolve_path(file_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return OperationResult(True, f"Wrote {len(content)} bytes", str(full_path))
        except Exception as e:
            return OperationResult(False, str(e))
    
    def append_file(self, file_path: str, content: str) -> OperationResult:
        try:
            full_path = self._resolve_path(file_path)
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(content)
            return OperationResult(True, f"Appended {len(content)} bytes")
        except Exception as e:
            return OperationResult(False, str(e))
    
    def delete_file(self, file_path: str) -> OperationResult:
        try:
            full_path = self._resolve_path(file_path)
            if not full_path.exists():
                return OperationResult(False, f"File not found: {file_path}")
            if full_path.is_dir():
                return OperationResult(False, "Use delete_project for directories")
            full_path.unlink()
            return OperationResult(True, f"Deleted {file_path}")
        except Exception as e:
            return OperationResult(False, str(e))
    
    def list_directory(self, dir_path: str = ".") -> List[FileInfo]:
        try:
            full_path = self._resolve_path(dir_path)
            if not full_path.exists() or not full_path.is_dir():
                return []
            return [
                FileInfo(
                    path=str(item.relative_to(self.workspace_root)),
                    name=item.name,
                    is_dir=item.is_dir(),
                    size=item.stat().st_size if item.is_file() else 0
                )
                for item in sorted(full_path.iterdir())
            ]
        except Exception:
            return []
    
    def create_directory(self, dir_path: str) -> OperationResult:
        try:
            full_path = self._resolve_path(dir_path)
            full_path.mkdir(parents=True, exist_ok=True)
            return OperationResult(True, f"Created directory: {dir_path}")
        except Exception as e:
            return OperationResult(False, str(e))
    
    def get_tree(self, dir_path: str = ".", max_depth: int = 3) -> str:
        try:
            full_path = self._resolve_path(dir_path)
            if not full_path.exists() or not full_path.is_dir():
                return f"Directory not found: {dir_path}"
            lines = [full_path.name + "/"]
            self._build_tree(full_path, "", lines, max_depth, 0)
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"
    
    def _build_tree(self, path: Path, prefix: str, lines: List[str], max_depth: int, depth: int) -> None:
        if depth >= max_depth:
            return
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._build_tree(item, new_prefix, lines, max_depth, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{item.name}")
    
    def search_files(self, pattern: str, dir_path: str = ".") -> List[str]:
        try:
            full_path = self._resolve_path(dir_path)
            matches = []
            for root, dirs, files in os.walk(full_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        file_path = Path(root) / filename
                        matches.append(str(file_path.relative_to(self.workspace_root)))
            return sorted(matches)
        except Exception:
            return []
    
    def grep(self, search_term: str, dir_path: str = ".", file_pattern: str = "*") -> List[str]:
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


_fs_instance: Optional[FileSystemTools] = None


def get_filesystem() -> FileSystemTools:
    global _fs_instance
    if _fs_instance is None:
        _fs_instance = FileSystemTools()
    return _fs_instance
