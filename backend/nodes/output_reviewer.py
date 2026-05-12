import json
import re
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from core.state import AgentState
from nodes.command_generator import chat_model


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = BACKEND_DIR / "prompts" / "reviewer_prompt.txt"


def load_reviewer_prompt() -> str:
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


def _fallback_review(state: AgentState) -> dict[str, Any]:
    exit_code = state.get("exit_code", state.get("returncode", 0))

    if exit_code == 0:
        return {
            "goal_achieved": True,
            "review_decision": "SUCCESS",
            "review_reasoning": "The command completed successfully, and the reviewer response could not be parsed.",
            "retry_command": "",
        }

    return {
        "goal_achieved": False,
        "review_decision": "FAILED",
        "review_reasoning": "The command failed, and the reviewer did not return a usable retry command.",
        "retry_command": "",
    }


def output_reviewer(state: AgentState) -> dict[str, Any]:
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    exit_code = state.get("exit_code", state.get("returncode", 0))

    messages = [
        SystemMessage(content=load_reviewer_prompt()),
        HumanMessage(
            content=(
                f"User goal:\n{state.get('user_input', '')}\n\n"
                f"Current working directory:\n{state.get('current_directory', '')}\n\n"
                f"Executed command:\n{state.get('command', '')}\n\n"
                f"stdout:\n{state.get('stdout', '')}\n\n"
                f"stderr:\n{state.get('stderr', '')}\n\n"
                f"exit_code:\n{exit_code}\n\n"
                f"retry_count: {retry_count}\n"
                f"max_retries: {max_retries}"
            )
        ),
    ]

    response = chat_model.invoke(messages)
    review = _extract_json(str(response.content))

    if not review:
        return _fallback_review(state)

    goal_achieved = bool(review.get("goal_achieved", False))
    retry_command = str(review.get("retry_command", "")).strip()
    review_decision = str(
        review.get("review_decision", "SUCCESS" if goal_achieved else "FAILED")
    ).upper()

    if goal_achieved:
        review_decision = "SUCCESS"
        retry_command = ""
    elif retry_command and retry_count < max_retries:
        review_decision = "RETRY"
    else:
        review_decision = "FAILED"
        retry_command = ""

    return {
        "goal_achieved": goal_achieved,
        "review_decision": review_decision,
        "review_reasoning": str(review.get("review_reasoning", "")).strip(),
        "retry_command": retry_command,
    }
