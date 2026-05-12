# Doer Terminal Agent

Doer is an AI-powered terminal command agent built with Python, Flask, LangGraph, LangChain, Hugging Face, and a lightweight browser UI.

The current workflow is:

```text
User request
-> get_environment
-> generate_command
-> execute_command
-> output_reviewer
-> retry_generate_command when needed
```

The reviewer checks both technical success and semantic task completion, then retries up to `max_retries`.

## Project Structure

```text
.
├── backend/
│   ├── api.py
│   ├── graph.py
│   ├── main.py
│   ├── core/
│   │   └── state.py
│   ├── nodes/
│   │   ├── command_executer.py
│   │   ├── command_generator.py
│   │   ├── get_environment.py
│   │   ├── output_reviewer.py
│   │   └── retry_generate_command.py
│   └── prompts/
│       ├── reviewer_prompt.txt
│       └── system_prompt.txt
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
└── .gitignore
```

## Run The Web App

From the project root:

```bash
source doerVenv/bin/activate
python backend/api.py
```

Open:

```text
http://127.0.0.1:5000
```

## API

- `GET /api/session` returns the current directory and in-memory chat messages.
- `POST /api/chat` runs the agent for one user message.
- `POST /api/reset` clears the current browser session.

Chat history is kept only in memory for the current Flask process.
