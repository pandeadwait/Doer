import os

from core.state import AgentState
from graph import app

def main() -> None:
    state: AgentState = {
        "current_directory": os.getcwd(),
        "command": "",
        "stdout": "",
        "stderr": "",
        "returncode": 0,
        "exit_code": 0,
        "goal_achieved": False,
        "review_decision": "",
        "review_reasoning": "",
        "retry_command": "",
        "retry_count": 0,
        "max_retries": 3,
    }

    while True:
        user_input = input(f"{state['current_directory']}\nEnter task:\n").strip()

        if not user_input:
            print("No task provided.")
            return

        state["user_input"] = user_input
        state["retry_count"] = 0
        state["goal_achieved"] = False
        state["review_decision"] = ""
        state["review_reasoning"] = ""
        state["retry_command"] = ""
        state = app.invoke(state) #type: ignore

        if state["stdout"]:
            print(state["stdout"])

        if state["stderr"]:
            print(state["stderr"])

        if not state.get("goal_achieved"):
            print(
                "Task not fully achieved "
                f"after {state.get('retry_count', 0)} retries: "
                f"{state.get('review_reasoning', 'No reviewer explanation available.')}"
            )


if __name__ == "__main__":
    main()
