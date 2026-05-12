from typing import Literal

from langgraph.graph import END, START, StateGraph

from core.state import AgentState
from nodes.command_executer import execute_command
from nodes.command_generator import generate_command
from nodes.get_environment import get_environment_info
from nodes.output_reviewer import output_reviewer
from nodes.retry_generate_command import retry_generate_command


def route_after_review(state: AgentState) -> Literal["retry_generate_command", "__end__"]:
    if state.get("goal_achieved"):
        return "__end__"

    if state.get("review_decision") != "RETRY":
        return "__end__"

    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        return "__end__"

    if not state.get("retry_command", "").strip():
        return "__end__"

    return "retry_generate_command"


graph = StateGraph(AgentState)

graph.add_node("get_environment_info", get_environment_info)
graph.add_node("generate_command", generate_command)
graph.add_node("execute_command", execute_command)
graph.add_node("output_reviewer", output_reviewer)
graph.add_node("retry_generate_command", retry_generate_command)

graph.add_edge(START, "get_environment_info")
graph.add_edge("get_environment_info", "generate_command")
graph.add_edge("generate_command", "execute_command")
graph.add_edge("execute_command", "output_reviewer")
graph.add_conditional_edges(
    "output_reviewer",
    route_after_review,
    {
        "retry_generate_command": "retry_generate_command",
        "__end__": END,
    },
)
graph.add_edge("retry_generate_command", "execute_command")

app = graph.compile()
