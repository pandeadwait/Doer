from typing import Literal

from langgraph.graph import END, START, StateGraph

from core.state import AgentState
from execution.bash_runner import execute_bash_script
from nodes.bash_script_generator import generate_bash_script
from nodes.command_executer import execute_command
from nodes.command_generator import generate_command
from nodes.get_environment import get_environment_info
from nodes.output_reviewer import output_reviewer
from nodes.retry_generate_command import retry_generate_command
from nodes.task_analyzer import analyze_task


def route_by_task_type(state: AgentState) -> Literal["single_command", "bash_script"]:
    if state.get("task_type") == "bash_script":
        return "bash_script"

    return "single_command"


def prepare_bash_retry(state: AgentState) -> dict[str, int]:
    return {"retry_count": state.get("retry_count", 0) + 1}


def route_after_review(
    state: AgentState,
) -> Literal["retry_generate_command", "retry_bash_script", "__end__"]:
    if state.get("goal_achieved"):
        return "__end__"

    if state.get("review_decision") != "RETRY":
        return "__end__"

    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return "__end__"

    if state.get("task_type") == "bash_script":
        return "retry_bash_script"

    if not state.get("retry_command", "").strip():
        return "__end__"

    return "retry_generate_command"


graph = StateGraph(AgentState)

graph.add_node("get_environment_info", get_environment_info)
graph.add_node("task_analyzer", analyze_task)
graph.add_node("generate_command", generate_command)
graph.add_node("execute_command", execute_command)
graph.add_node("generate_bash_script", generate_bash_script)
graph.add_node("execute_bash_script", execute_bash_script)
graph.add_node("output_reviewer", output_reviewer)
graph.add_node("retry_generate_command", retry_generate_command)
graph.add_node("retry_bash_script", prepare_bash_retry)

graph.add_edge(START, "get_environment_info")
graph.add_edge("get_environment_info", "task_analyzer")
graph.add_conditional_edges(
    "task_analyzer",
    route_by_task_type,
    {
        "single_command": "generate_command",
        "bash_script": "generate_bash_script",
    },
)
graph.add_edge("generate_command", "execute_command")
graph.add_edge("execute_command", "output_reviewer")
graph.add_edge("generate_bash_script", "execute_bash_script")
graph.add_edge("execute_bash_script", "output_reviewer")
graph.add_conditional_edges(
    "output_reviewer",
    route_after_review,
    {
        "retry_generate_command": "retry_generate_command",
        "retry_bash_script": "retry_bash_script",
        "__end__": END,
    },
)
graph.add_edge("retry_generate_command", "execute_command")
graph.add_edge("retry_bash_script", "generate_bash_script")

app = graph.compile()
