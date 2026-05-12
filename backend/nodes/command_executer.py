import os
import shlex
import subprocess
from pathlib import Path

from core.state import AgentState


def execute_command(state: AgentState) -> dict:
    command = state["command"]
    current_directory = state["current_directory"]

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return {
            "stdout": "",
            "stderr": f"Invalid shell command: {exc}",
            "returncode": 2,
            "exit_code": 2,
        }

    if parts and parts[0] == "cd":
        target = parts[1] if len(parts) > 1 else os.path.expanduser("~")
        next_directory = Path(target).expanduser()

        if not next_directory.is_absolute():
            next_directory = Path(current_directory) / next_directory

        next_directory = next_directory.resolve()

        if not next_directory.is_dir():
            return {
                "returncode": 1,
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Not a directory: {next_directory}",
            }

        return {
            "current_directory": str(next_directory),
            "returncode": 0,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=current_directory,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return {
            "stdout": "",
            "stderr": f"Command execution failed: {exc}",
            "returncode": 1,
            "exit_code": 1,
        }

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "exit_code": result.returncode,
    }
