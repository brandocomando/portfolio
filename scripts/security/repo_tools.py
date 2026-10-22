#!/usr/bin/env python3
"""
Repository Exploration & HCL/Code Inspection Tooling for the LangGraph Security Agent.
Provides dynamic, zero-maintenance tools that allow the LLM to autonomously
discover directories, search code/infrastructure patterns, read files, and parse
Terraform (.tf) definitions on demand without hardcoded directory paths.
"""
import fnmatch
import json
import os
import re
from typing import Any
import hcl2

IGNORED_DIRS = {
    ".git",
    ".terraform",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".worktrees",
    "dist",
    "build",
}


def _safe_resolve(repo_root: str, rel_path: str) -> str:
    """Resolves a path inside repo_root and prevents directory traversal outside the repo."""
    abs_root = os.path.abspath(repo_root)
    target = os.path.abspath(os.path.join(abs_root, rel_path.lstrip("/")))
    if not (target == abs_root or target.startswith(abs_root + os.sep)):
        raise ValueError(f"Path '{rel_path}' escapes repository root.")
    return target


def strip_hcl_quotes(val: Any) -> Any:
    """Recursively strips extra outer quotes added by python-hcl2 v8+."""
    if isinstance(val, str):
        if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        return val
    if isinstance(val, list):
        return [strip_hcl_quotes(item) for item in val]
    if isinstance(val, dict):
        return {
            strip_hcl_quotes(k): strip_hcl_quotes(v)
            for k, v in val.items()
            if k not in {"__is_block__", "__comments__"}
        }
    return val


def list_repo_files(repo_root: str, subdir: str = ".", glob_pattern: str = "*") -> str:
    """
    Lists files in the repository matching an optional subdirectory and glob pattern.
    Allows the agent to dynamically discover any new modules, services, or directories.
    """
    try:
        start_dir = _safe_resolve(repo_root, subdir)
    except ValueError as e:
        return f"Error: {e}"

    if not os.path.exists(start_dir):
        return f"Directory '{subdir}' does not exist."

    matched = []
    for root, dirs, files in os.walk(start_dir):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), repo_root)
            if fnmatch.fnmatch(f, glob_pattern) or fnmatch.fnmatch(rel, glob_pattern):
                matched.append(rel)
                if len(matched) >= 250:
                    break
        if len(matched) >= 250:
            break

    return json.dumps({"directory": subdir, "pattern": glob_pattern, "files": matched}, indent=2)


def search_codebase(
    repo_root: str,
    regex_query: str,
    file_glob: str = "*",
    max_matches: int = 40,
) -> str:
    """
    Searches across the repository for a regex pattern (e.g., SDK usage, IAM roles,
    route decorators, secret references, middleware classes) and returns matching
    file paths, line numbers, and code snippets.
    """
    try:
        pattern = re.compile(regex_query, re.IGNORECASE)
    except re.error as e:
        return f"Invalid regex '{regex_query}': {e}"

    results = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), repo_root)
            if file_glob != "*" and not (
                fnmatch.fnmatch(f, file_glob) or fnmatch.fnmatch(rel, file_glob)
            ):
                continue
            full_path = os.path.join(root, f)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    for idx, line in enumerate(fh, start=1):
                        if pattern.search(line):
                            results.append(
                                {
                                    "file": rel,
                                    "line": idx,
                                    "snippet": line.strip()[:240],
                                }
                            )
                            if len(results) >= max_matches:
                                return json.dumps(
                                    {"query": regex_query, "matches": results, "truncated": True},
                                    indent=2,
                                )
            except Exception:
                continue

    return json.dumps({"query": regex_query, "matches": results, "truncated": False}, indent=2)


def read_repo_file(
    repo_root: str,
    file_path: str,
    start_line: int = 1,
    end_line: int = 200,
) -> str:
    """
    Reads a slice of lines from any file in the repository so the agent can inspect
    implementation details, route handlers, middleware logic, or Terraform modules.
    """
    try:
        target = _safe_resolve(repo_root, file_path)
    except ValueError as e:
        return f"Error: {e}"

    if not os.path.isfile(target):
        return f"File '{file_path}' not found."

    start_line = max(1, int(start_line))
    end_line = max(start_line, min(int(end_line), start_line + 300))

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        selected = lines[start_line - 1 : end_line]
        numbered = "".join(
            f"{idx}: {line}" for idx, line in enumerate(selected, start=start_line)
        )
        return (
            f"--- {file_path} (lines {start_line}-{min(end_line, len(lines))} of {len(lines)}) ---\n"
            + numbered[:12000]
        )
    except Exception as e:
        return f"Error reading '{file_path}': {e}"


def parse_terraform_hcl(repo_root: str, tf_path: str = ".") -> str:
    """
    Parses a specific `.tf` file or all `.tf` files under a directory into structured
    JSON using `python-hcl2` so the agent can inspect resources, IAM bindings,
    variables, and module compositions.
    """
    try:
        target = _safe_resolve(repo_root, tf_path)
    except ValueError as e:
        return f"Error: {e}"

    tf_files = []
    if os.path.isfile(target) and target.endswith(".tf"):
        tf_files.append(target)
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
            for f in sorted(files):
                if f.endswith(".tf"):
                    tf_files.append(os.path.join(root, f))
    else:
        return f"No Terraform files found at '{tf_path}'."

    parsed_files = {}
    for path in tf_files[:25]:
        rel = os.path.relpath(path, repo_root)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                parsed_files[rel] = strip_hcl_quotes(hcl2.load(fh))
        except Exception as e:
            parsed_files[rel] = {"parse_error": str(e)}

    return json.dumps(parsed_files, indent=2)[:15000]


def make_agent_tools(repo_root: str) -> dict[str, Any]:
    """
    Creates Gemini-compatible tool declarations and a dispatcher bound to `repo_root`.
    """
    def list_files(subdir: str = ".", glob_pattern: str = "*") -> str:
        """List files in the repository under `subdir` matching `glob_pattern`."""
        return list_repo_files(repo_root, subdir=subdir, glob_pattern=glob_pattern)

    def search_code(regex_query: str, file_glob: str = "*") -> str:
        """Search across the repository for `regex_query` (e.g., SDK usage, IAM roles, routes, secrets)."""
        return search_codebase(repo_root, regex_query=regex_query, file_glob=file_glob)

    def read_file(file_path: str, start_line: int = 1, end_line: int = 200) -> str:
        """Read lines `start_line` to `end_line` of `file_path` in the repository."""
        return read_repo_file(repo_root, file_path=file_path, start_line=start_line, end_line=end_line)

    def inspect_terraform(tf_path: str = "infra") -> str:
        """Parse `.tf` file or directory `tf_path` into structured HCL2 JSON."""
        return parse_terraform_hcl(repo_root, tf_path=tf_path)

    return {
        "functions": [list_files, search_code, read_file, inspect_terraform],
        "dispatch": {
            "list_files": list_files,
            "search_code": search_code,
            "read_file": read_file,
            "inspect_terraform": inspect_terraform,
        },
    }
