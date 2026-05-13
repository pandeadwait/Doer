import json
import re
from pathlib import Path
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage

from core.state import AgentState
from nodes.command_generator import chat_model


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = BACKEND_DIR / "prompts" / "task_analyzer_prompt.txt"

TaskType = Literal["single_command", "bash_script"]

BASH_SCRIPT_SIGNALS = (
    " for each ",
    " every ",
    " then ",
    " after ",
    " before ",
    " compress",
    " archive",
    " backup",
    " report",
    " summary",
    " older than ",
    " convert",
    " transform",
    " move ",
    " copy ",
    " rename",
    " organize",
    " recursively",
)

SINGLE_COMMAND_STARTS = (
    "list ",
    "show ",
    "find ",
    "search ",
    "check ",
    "print ",
    "display ",
    "count ",
    "where ",
    "which ",
)


def load_task_analyzer_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    return parsed if isinstance(parsed, dict) else {}


def _heuristic_task_type(user_input: str) -> TaskType:
    normalized = f" {user_input.lower().strip()} "
    signal_count = sum(signal in normalized for signal in BASH_SCRIPT_SIGNALS)
    operation_words = sum(
        word in normalized
        for word in (
            " find ",
            " compress",
            " move ",
            " create ",
            " generate ",
            " convert",
            " copy ",
            " backup",
            " archive",
        )
    )

    if " and " in normalized and operation_words >= 2:
        return "bash_script"

    if signal_count >= 2 or (signal_count >= 1 and operation_words >= 2):
        return "bash_script"

    if any(normalized.strip().startswith(prefix) for prefix in SINGLE_COMMAND_STARTS):
        return "single_command"

    return "single_command"


def _normalize_task_type(value: object) -> TaskType | None:
    task_type = str(value).strip().lower()
    if task_type in {"single_command", "bash_script"}:
        return task_type  # type: ignore[return-value]
    return None


def analyze_task(state: AgentState) -> dict[str, str]:
    user_input = state.get("user_input", "")
    heuristic_type = _heuristic_task_type(user_input)

    messages = [
        SystemMessage(content=load_task_analyzer_prompt()),
        HumanMessage(
            content=(
                f"Current working directory: {state.get('current_directory', '')}\n"
                f"User task: {user_input}\n"
                f"Heuristic recommendation: {heuristic_type}"
            )
        ),
    ]

    try:
        response = chat_model.invoke(messages)
        parsed = _extract_json(str(response.content))
    except Exception:
        parsed = {}

    task_type = _normalize_task_type(parsed.get("task_type")) or heuristic_type

    if heuristic_type == "bash_script":
        task_type = "bash_script"

    return {
        "task_type": task_type,
        "bash_script": "",
        "script_path": "",
    }
