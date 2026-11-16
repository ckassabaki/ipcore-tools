"""Crawler for GitHub repositories"""

from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import db_tools_registry as db


def get_remote_url(repo_path: Path) -> str:
    """Get git remote URL for a repository."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_readme_description(repo_path: Path) -> str:
    """Extract first meaningful line from README."""
    for readme_file in ["README.md", "README.txt", "README"]:
        readme_path = repo_path / readme_file
        if readme_path.exists():
            try:
                with open(readme_path, encoding="utf-8") as f:
                    lines = f.readlines()

                # Find first non-empty, non-header line
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and len(line) > 10:
                        return line[:200]  # Max 200 chars

                # Fallback to first line
                if lines:
                    return lines[0].strip().strip("#").strip()[:200]

            except Exception:
                pass

    return f"Git repository: {repo_path.name}"


def scan_single_repo(repo_url_or_path: str) -> list:
    """
    Scan a single repository (for smart import).

    Args:
        repo_url_or_path: GitHub URL or local path

    Returns:
        List of discovered tools
    """
    # For now, return basic info - can be enhanced later
    return [{
        "name": repo_url_or_path.split("/")[-1],
        "description": f"GitHub repository: {repo_url_or_path}",
        "tool_type": "other",
        "access_url": repo_url_or_path,
        "access_method": "github",
        "tags": "github,repository",
    }]


def crawl_github_repos(search_dir: Path = None, max_depth: int = 3) -> int:
    """
    Find .git directories and extract repo metadata.

    Args:
        search_dir: Directory to search (defaults to home directory)
        max_depth: Maximum directory depth to search

    Returns:
        Number of repositories discovered
    """
    if search_dir is None:
        search_dir = Path.home()

    discovered_tools = []

    # Find all .git directories (limit depth to avoid slow scans)
    try:
        # Use glob with limited depth
        git_dirs = list(search_dir.glob("*/.git"))  # Depth 1
        if max_depth >= 2:
            git_dirs.extend(search_dir.glob("*/*/.git"))  # Depth 2
        if max_depth >= 3:
            git_dirs.extend(search_dir.glob("*/*/*/.git"))  # Depth 3

    except Exception as e:
        print(f"Failed to search for git repos: {e}")
        return 0

    for git_dir in git_dirs:
        repo_path = git_dir.parent

        # Skip hidden directories and common exclude patterns
        if any(part.startswith(".") for part in repo_path.parts):
            if repo_path.name not in [".claude", "ipcore-tools"]:  # Allow some hidden dirs
                continue

        try:
            remote_url = get_remote_url(repo_path)
            description = get_readme_description(repo_path)

            tool_data = {
                "name": repo_path.name,
                "description": description,
                "tool_type": "other",  # Will be refined by categorization
                "access_url": remote_url,
                "access_method": "github",
                "config_path": str(repo_path),
                "tags": "github,repository",
                "source": "crawler:github",
            }

            discovered_tools.append(tool_data)

        except Exception as e:
            print(f"Failed to process {repo_path}: {e}")
            continue

    # Bulk insert/update
    for tool in discovered_tools:
        db.add_or_update_tool(tool)

    return len(discovered_tools)


if __name__ == "__main__":
    count = crawl_github_repos()
    print(f"✅ Discovered {count} GitHub repositories")
