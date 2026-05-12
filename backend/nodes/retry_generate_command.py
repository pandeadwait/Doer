from core.state import AgentState


def retry_generate_command(state: AgentState) -> dict:
    retry_command = state.get("retry_command", "").strip()

    return {
        "command": retry_command or state.get("command", ""),
        "retry_count": state.get("retry_count", 0) + 1,
    }
