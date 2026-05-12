import os

from core.state import AgentState


def get_environment_info(state: AgentState) -> dict[str, str]:
    return {"current_directory": state.get("current_directory", os.getcwd())}
