import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from core.state import AgentState


def execute_bash_script(state: AgentState) -> dict[str, Any]:
    script = state.get("bash_script", "").strip()
    current_directory = Path(state["current_directory"]).resolve()

    if not script:
        return {
            "stdout": "",
            "stderr": "No bash script was generated.",
            "returncode": 2,
            "exit_code": 2,
            "script_path": "",
        }

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="doer_",
            suffix=".sh",
            dir=current_directory,
            delete=False,
        ) as script_file:
            script_file.write(script)
            script_file.write("\n")
            script_path = Path(script_file.name)

        os.chmod(script_path, 0o700)

        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=current_directory,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return {
            "stdout": "",
            "stderr": f"Bash script execution failed: {exc}",
            "returncode": 1,
            "exit_code": 1,
            "script_path": str(locals().get("script_path", "")),
        }

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "exit_code": result.returncode,
        "script_path": str(script_path),
        "command": f"bash {script_path}",
    }
