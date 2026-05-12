import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from core.state import AgentState


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = BACKEND_DIR / "prompts" / "system_prompt.txt"

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

llm = HuggingFaceEndpoint(
    repo_id=os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-Coder-32B-Instruct"),
    task="text-generation",
    max_new_tokens=128,
    do_sample=False,
    repetition_penalty=1.03,
    provider=os.getenv("HF_PROVIDER", "auto"),
) #type: ignore

chat_model = ChatHuggingFace(llm=llm)


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def generate_command(state: AgentState) -> dict[str, str]:
    messages = [
        SystemMessage(content=load_system_prompt()),
        HumanMessage(content=(
                f'Current working directory: {state["current_directory"]}\n'
                f'User task: {state["user_input"]}'
            )
        ),
    ]

    response = chat_model.invoke(messages)
    command = str(response.content).strip()

    return {
        "command": command,
        "goal_achieved": False,
        "review_decision": "",
        "review_reasoning": "",
        "retry_command": "",
    }
