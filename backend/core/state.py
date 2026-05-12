from typing import TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    current_directory: str
    command: str
    stdout: str
    stderr: str
    returncode: int
    exit_code: int
    review_decision: str
    review_reasoning: str
    goal_achieved: bool
    retry_command: str
    retry_count: int
    max_retries: int
