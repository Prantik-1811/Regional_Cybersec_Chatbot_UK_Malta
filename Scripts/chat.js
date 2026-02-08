// =====================================
// CONFIG
// =====================================
const API_ENDPOINT = "http://localhost:8000/api/chat";
const REGION = location.pathname.includes("malta") ? "malta" : "uk";

// =====================================
// STATE
// =====================================
let chats = JSON.parse(localStorage.getItem("chats")) || [];
let activeChatId = localStorage.getItem("activeChatId") || null;

// =====================================
// DOM
// =====================================
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("chatInput");
const chatListEl = document.getElementById("chatList");

// =====================================
// INIT
// =====================================
if (!activeChatId || !chats.find(c => c.id === activeChatId)) {
  createNewChat();
} else {
  renderSidebar();
  loadChat(activeChatId);
}

// =====================================
// CHAT CREATION
// =====================================
function createNewChat() {
  const chat = {
    id: `chat_${Date.now()}`,
    title: "New Chat",
    messages: [
      { sender: "bot", text: "Hello! How can I help you?" }
    ]
  };

  chats.unshift(chat);
  activeChatId = chat.id;
  saveState();

  renderSidebar();
  loadChat(chat.id);
}

// =====================================
// RENDER SIDEBAR
// =====================================
function renderSidebar() {
  chatListEl.innerHTML = "";

  chats.forEach(chat => {
    const li = document.createElement("li");
    li.textContent = chat.title;
    li.className = chat.id === activeChatId ? "active" : "";

    li.onclick = () => {
      activeChatId = chat.id;
      saveState();
      renderSidebar();
      loadChat(chat.id);
    };

    chatListEl.appendChild(li);
  });
}function renderSidebar() {
  chatListEl.innerHTML = "";

  // sort: pinned first, then newest
  const sortedChats = [...chats].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return 0;
  });

  sortedChats.forEach(chat => {
    const li = document.createElement("li");
    li.className = chat.id === activeChatId ? "active" : "";
    if (chat.pinned) li.classList.add("pinned");

    const container = document.createElement("div");
    container.className = "chat-item";

    const title = document.createElement("span");
    title.className = "chat-title";
    title.textContent = chat.title;
    title.onclick = () => {
      activeChatId = chat.id;
      saveState();
      renderSidebar();
      loadChat(chat.id);
    };

    const actions = document.createElement("div");
    actions.className = "chat-actions";

    //  Pin / Unpin
    const pinBtn = document.createElement("button");
    pinBtn.innerText = chat.pinned ? "📌" : "📍";
    pinBtn.title = chat.pinned ? "Unpin chat" : "Pin chat";
    pinBtn.onclick = (e) => {
      e.stopPropagation();
      chat.pinned = !chat.pinned;
      saveState();
      renderSidebar();
    };

    //  Delete
    const delBtn = document.createElement("button");
    delBtn.innerText = "🗑️";
    delBtn.title = "Delete chat";
    delBtn.onclick = (e) => {
      e.stopPropagation();
      deleteChat(chat.id);
    };

    actions.appendChild(pinBtn);
    actions.appendChild(delBtn);

    container.appendChild(title);
    container.appendChild(actions);

    li.appendChild(container);
    chatListEl.appendChild(li);
  });
}


// =====================================
// LOAD CHAT
// =====================================
function loadChat(chatId) {
  messagesEl.innerHTML = "";

  const chat = chats.find(c => c.id === chatId);
  if (!chat) return;

  chat.messages.forEach(msg => {
    addMessage(msg.text, msg.sender);
  });
}

// =====================================
// MESSAGE HELPERS
// =====================================
function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.textContent = text;
  messagesEl.appendChild(msg);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// =====================================
// SEND MESSAGE
// =====================================
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  const chat = chats.find(c => c.id === activeChatId);
  if (!chat) return;

  // User message
  chat.messages.push({ sender: "user", text });
  addMessage(text, "user");
  inputEl.value = "";

  // Update title (first user msg)
  if (chat.title === "New Chat") {
    chat.title = text.slice(0, 30);
  }

  renderSidebar();
  saveState();

  // Typing indicator
  const typing = document.createElement("div");
  typing.className = "message bot";
  typing.textContent = "Typing...";
  messagesEl.appendChild(typing);

  try {
    const res = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, region: REGION })
    });

    const data = await res.json();
    typing.remove();

    chat.messages.push({ sender: "bot", text: data.reply });
    addMessage(data.reply, "bot");
    saveState();

  } catch (err) {
    typing.remove();
    addMessage("Server error. Please try again.", "bot");
  }
}

// =====================================
// ENTER KEY
// =====================================
function handleEnter(e) {
  if (e.key === "Enter") sendMessage();
}

// =====================================
// THEME
// =====================================
function toggleTheme() {
  const html = document.documentElement;
  const next = html.dataset.theme === "dark" ? "light" : "dark";
  html.dataset.theme = next;
  localStorage.setItem("theme", next);
}

(function () {
  const saved = localStorage.getItem("theme");
  if (saved) document.documentElement.dataset.theme = saved;
})();

// =====================================
// STORAGE
// =====================================
function saveState() {
  localStorage.setItem("chats", JSON.stringify(chats));
  localStorage.setItem("activeChatId", activeChatId);
}

function deleteChat(chatId) {
  const index = chats.findIndex(c => c.id === chatId);
  if (index === -1) return;

  chats.splice(index, 1);

  if (activeChatId === chatId) {
    activeChatId = chats.length ? chats[0].id : null;
    if (activeChatId) loadChat(activeChatId);
    else createNewChat();
  }

  saveState();
  renderSidebar();
}

const chat = {
  id: `chat_${Date.now()}`,
  title: "New Chat",
  messages: [
    { sender: "bot", text: "Hello! How can I help you?" }
  ],
  pinned: false
};
