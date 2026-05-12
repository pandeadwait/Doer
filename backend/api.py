import os
import uuid
from threading import Lock
from typing import Any

from flask import Flask, jsonify, request, send_from_directory, session

from core.state import AgentState
from graph import app as agent_app


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

flask_app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/static")
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-terminal-agent-secret")

session_lock = Lock()
session_store: dict[str, AgentState] = {}
chat_store: dict[str, list[dict[str, Any]]] = {}


def _new_state() -> AgentState:
    return {
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


def _session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return str(session["session_id"])


def _get_session_state() -> tuple[str, AgentState]:
    session_id = _session_id()

    with session_lock:
        if session_id not in session_store:
            session_store[session_id] = _new_state()
            chat_store[session_id] = []

        return session_id, session_store[session_id]


def _reset_for_user_input(state: AgentState, user_input: str) -> None:
    state["user_input"] = user_input
    state["retry_count"] = 0
    state["goal_achieved"] = False
    state["review_decision"] = ""
    state["review_reasoning"] = ""
    state["retry_command"] = ""
    state["stdout"] = ""
    state["stderr"] = ""
    state["returncode"] = 0
    state["exit_code"] = 0


def _assistant_content(state: AgentState) -> str:
    parts: list[str] = []

    if state.get("stdout"):
        parts.append(state["stdout"].strip())

    if state.get("stderr"):
        parts.append(state["stderr"].strip())

    if not parts:
        if state.get("goal_achieved"):
            parts.append("Command completed successfully.")
        else:
            parts.append("No command output.")

    if not state.get("goal_achieved"):
        reasoning = state.get("review_reasoning") or "No reviewer explanation available."
        parts.append(
            f"Task not fully achieved after {state.get('retry_count', 0)} retries: {reasoning}"
        )

    return "\n\n".join(parts)


def _public_state(session_id: str, state: AgentState) -> dict[str, Any]:
    return {
        "current_directory": state.get("current_directory", os.getcwd()),
        "messages": chat_store.get(session_id, []),
    }


@flask_app.get("/")
def index() -> Any:
    return send_from_directory(FRONTEND_DIR, "index.html")


@flask_app.get("/api/session")
def get_session() -> Any:
    session_id, state = _get_session_state()
    return jsonify(_public_state(session_id, state))


@flask_app.post("/api/chat")
def chat() -> Any:
    payload = request.get_json(silent=True) or {}
    user_input = str(payload.get("message", "")).strip()

    if not user_input:
        return jsonify({"error": "Message is required."}), 400

    session_id, state = _get_session_state()

    user_message = {
        "role": "user",
        "content": user_input,
    }

    _reset_for_user_input(state, user_input)

    try:
        result_state = agent_app.invoke(state)  # type: ignore[assignment]
    except Exception as exc:
        result_state = {
            **state,
            "goal_achieved": False,
            "review_decision": "FAILED",
            "review_reasoning": f"Agent execution failed: {exc}",
            "stdout": "",
            "stderr": str(exc),
        }

    assistant_message = {
        "role": "assistant",
        "content": _assistant_content(result_state),
        "command": result_state.get("command", ""),
        "stdout": result_state.get("stdout", ""),
        "stderr": result_state.get("stderr", ""),
        "exit_code": result_state.get("exit_code", result_state.get("returncode", 0)),
        "goal_achieved": result_state.get("goal_achieved", False),
        "review_decision": result_state.get("review_decision", ""),
        "review_reasoning": result_state.get("review_reasoning", ""),
        "retry_count": result_state.get("retry_count", 0),
        "max_retries": result_state.get("max_retries", 3),
    }

    with session_lock:
        session_store[session_id] = result_state
        chat_store.setdefault(session_id, []).extend([user_message, assistant_message])

    return jsonify(
        {
            **_public_state(session_id, result_state),
            "latest": assistant_message,
        }
    )


@flask_app.post("/api/reset")
def reset_session() -> Any:
    session_id = _session_id()

    with session_lock:
        session_store[session_id] = _new_state()
        chat_store[session_id] = []

    return jsonify(_public_state(session_id, session_store[session_id]))


if __name__ == "__main__":
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
