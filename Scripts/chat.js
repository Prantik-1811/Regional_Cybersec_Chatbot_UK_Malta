// ================================
// CONFIG
// ================================
const API_ENDPOINT = "http://localhost:8000/api/chat"; 
// change when deploying

// Detect region from URL
const REGION = window.location.pathname.includes("malta")
  ? "malta"
  : "uk";

// ================================
// DOM ELEMENTS
// ================================
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("chatInput");

// ================================
// HELPERS
// ================================
function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.textContent = text;
  messagesEl.appendChild(msg);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addTypingIndicator() {
  const typing = document.createElement("div");
  typing.className = "message bot";
  typing.id = "typing-indicator";
  typing.textContent = "Typing...";
  messagesEl.appendChild(typing);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeTypingIndicator() {
  const typing = document.getElementById("typing-indicator");
  if (typing) typing.remove();
}

// ================================
// SEND MESSAGE
// ================================
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  // Show user message
  addMessage(text, "user");
  inputEl.value = "";

  // Show typing indicator
  addTypingIndicator();

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        region: REGION
      })
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();

    removeTypingIndicator();
    addMessage(data.reply, "bot");

  } catch (error) {
    removeTypingIndicator();
    addMessage(
      "Sorry, I couldn't reach the server. Please try again.",
      "bot"
    );
    console.error(error);
  }
}

// ================================
// ENTER KEY HANDLER
// ================================
function handleEnter(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
}

// ================================
// THEME TOGGLE
// ================================
function toggleTheme() {
  const html = document.documentElement;
  const newTheme =
    html.dataset.theme === "dark" ? "light" : "dark";

  html.dataset.theme = newTheme;
  localStorage.setItem("theme", newTheme);
}

// Load saved theme
(function loadTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    document.documentElement.dataset.theme = saved;
  }
})();
