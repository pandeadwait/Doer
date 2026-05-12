const directoryEl = document.querySelector("#current-directory");
const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chat-form");
const inputEl = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const template = document.querySelector("#message-template");

let messages = [];

function setDirectory(path) {
  directoryEl.textContent = path || "Unknown";
  directoryEl.title = path || "";
}

function showEmptyState() {
  messagesEl.innerHTML = "";
  const empty = document.createElement("p");
  empty.className = "empty-state";
  empty.textContent = "Ask for a terminal task to begin.";
  messagesEl.append(empty);
}

function renderMessages() {
  if (!messages.length) {
    showEmptyState();
    return;
  }

  messagesEl.innerHTML = "";

  for (const message of messages) {
    const item = template.content.firstElementChild.cloneNode(true);
    const role = message.role === "user" ? "You" : "Agent";
    const status = item.querySelector(".status");
    const details = item.querySelector(".details");

    item.classList.add(message.role);
    item.querySelector(".role").textContent = role;
    item.querySelector(".content").textContent = message.content || "";

    if (message.role === "assistant") {
      const achieved = Boolean(message.goal_achieved);
      status.textContent = achieved ? "Achieved" : message.review_decision || "Review";
      status.classList.toggle("failed", !achieved);
      item.querySelector(".command").textContent = message.command || "";
      item.querySelector(".exit-code").textContent = String(message.exit_code ?? "");
      item.querySelector(".retries").textContent = `${message.retry_count ?? 0} / ${message.max_retries ?? 3}`;
      item.querySelector(".review").textContent = message.review_reasoning || "";
    } else {
      status.textContent = "";
      details.hidden = true;
    }

    messagesEl.append(item);
  }

  messagesEl.lastElementChild?.scrollIntoView({ block: "end" });
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  inputEl.disabled = isBusy;
  sendButton.textContent = isBusy ? "Running" : "Send";
}

function autosizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${inputEl.scrollHeight}px`;
}

async function loadSession() {
  const response = await fetch("/api/session");
  const data = await response.json();

  setDirectory(data.current_directory);
  messages = data.messages || [];
  renderMessages();
}

async function sendMessage(message) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }

  setDirectory(data.current_directory);
  messages = data.messages || [];
  renderMessages();
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = inputEl.value.trim();
  if (!message) {
    return;
  }

  messages = [
    ...messages,
    {
      role: "user",
      content: message,
    },
    {
      role: "assistant",
      content: "Running command...",
      review_decision: "RUNNING",
    },
  ];
  renderMessages();

  inputEl.value = "";
  autosizeInput();
  setBusy(true);

  try {
    await sendMessage(message);
  } catch (error) {
    messages = [
      ...messages.slice(0, -1),
      {
        role: "assistant",
        content: error.message,
        goal_achieved: false,
        review_decision: "FAILED",
      },
    ];
    renderMessages();
  } finally {
    setBusy(false);
    inputEl.focus();
  }
});

inputEl.addEventListener("input", autosizeInput);

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

loadSession().catch((error) => {
  messages = [
    {
      role: "assistant",
      content: error.message,
      goal_achieved: false,
      review_decision: "FAILED",
    },
  ];
  renderMessages();
});
