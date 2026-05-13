import re
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from core.state import AgentState
from nodes.command_generator import chat_model


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = BACKEND_DIR / "prompts" / "bash_script_prompt.txt"


def load_bash_script_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:bash|sh)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    return cleaned.strip()


def _ensure_shebang(script: str) -> str:
    if script.startswith("#!/bin/bash"):
        return script

    return "#!/bin/bash\n" + script.lstrip()


def generate_bash_script(state: AgentState) -> dict[str, str | bool]:
    messages = [
        SystemMessage(content=load_bash_script_prompt()),
        HumanMessage(
            content=(
                f"Current working directory: {state.get('current_directory', '')}\n"
                f"User task: {state.get('user_input', '')}\n\n"
                f"Previous stdout:\n{state.get('stdout', '')}\n\n"
                f"Previous stderr:\n{state.get('stderr', '')}\n\n"
                f"Reviewer feedback:\n{state.get('review_reasoning', '')}"
            )
        ),
    ]

    response = chat_model.invoke(messages)
    script = _ensure_shebang(_strip_code_fence(str(response.content)))

    return {
        "bash_script": script,
        "command": "bash <generated_script>",
        "script_path": "",
        "goal_achieved": False,
        "review_decision": "",
        "review_reasoning": "",
        "retry_command": "",
    }
