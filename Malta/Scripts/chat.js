// =====================================
// CONFIGURATION
// =====================================
// API endpoint for the chatbot backend.
const API_ENDPOINT = "http://localhost:8000/api/chat";

// Determine the region based on the URL path.
// Defaults to "uk" if "malta" is not in the path.
const REGION = location.pathname.includes("malta") ? "malta" : "uk";

// =====================================
// STATE MANAGEMENT
// =====================================
// Retrieve saved chats from local storage or initialize an empty array.
let chats = JSON.parse(localStorage.getItem("chats")) || [];

// Retrieve the ID of the currently active chat from local storage.
let activeChatId = localStorage.getItem("activeChatId") || null;

// =====================================
// DOM ELEMENTS
// =====================================
// Cache references to key DOM elements for performance.
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("chatInput");
const chatListEl = document.getElementById("chatList");

// =====================================
// INITIALIZATION
// =====================================
// Check if there is an active chat and if it exists in the loaded chats.
// If not, create a new chat session.
if (!activeChatId || !chats.find(c => c.id === activeChatId)) {
  createNewChat();
} else {
  // Otherwise, render the sidebar and load the active chat.
  renderSidebar();
  loadChat(activeChatId);
}

// =====================================
// CHAT OPERATIONS
// =====================================

/**
 * Creates a new chat session.
 * Initializes a new chat object with a default welcome message.
 * Updates the state and UI.
 */
function createNewChat() {
  const chat = {
    id: `chat_${Date.now()}`, // Unique ID based on timestamp
    title: "New Chat",
    messages: [
      { sender: "bot", text: "Hello! How can I help you?" }
    ],
    pinned: false // Default pinned state
  };

  // Add the new chat to the beginning of the list.
  chats.unshift(chat);
  activeChatId = chat.id;

  // Persist changes to local storage.
  saveState();

  // Update UI.
  renderSidebar();
  loadChat(chat.id);
}

/**
 * Renders the sidebar chat list.
 * Handles sorting (pinned first) and creating UI elements for each chat.
 */
function renderSidebar() {
  chatListEl.innerHTML = "";

  // Sort chats: Pinned chats first, then by original order (newest first).
  const sortedChats = [...chats].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1; // a comes first
    if (!a.pinned && b.pinned) return 1;  // b comes first
    return 0; // unchanged
  });

  // Iterate through sorted chats and create list items.
  sortedChats.forEach(chat => {
    const li = document.createElement("li");
    // Highlight the active chat.
    li.className = chat.id === activeChatId ? "active" : "";
    if (chat.pinned) li.classList.add("pinned");

    const container = document.createElement("div");
    container.className = "chat-item";

    // Chat Title Element
    const title = document.createElement("span");
    title.className = "chat-title";
    title.textContent = chat.title;

    // Switch to this chat when title is clicked.
    title.onclick = () => {
      activeChatId = chat.id;
      saveState();
      renderSidebar();
      loadChat(chat.id);
    };

    // Chat Actions (Pin, Delete)
    const actions = document.createElement("div");
    actions.className = "chat-actions";

    // Pin/Unpin Button
    const pinBtn = document.createElement("button");
    pinBtn.innerText = chat.pinned ? "📌" : "📍";
    pinBtn.title = chat.pinned ? "Unpin chat" : "Pin chat";
    pinBtn.onclick = (e) => {
      e.stopPropagation(); // Prevent triggering the list item click
      chat.pinned = !chat.pinned;
      saveState();
      renderSidebar();
    };

    // Delete Button
    const delBtn = document.createElement("button");
    delBtn.innerText = "🗑️";
    delBtn.title = "Delete chat";
    delBtn.onclick = (e) => {
      e.stopPropagation(); // Prevent triggering the list item click
      deleteChat(chat.id);
    };

    // Assemble the elements.
    actions.appendChild(pinBtn);
    actions.appendChild(delBtn);

    container.appendChild(title);
    container.appendChild(actions);

    li.appendChild(container);
    chatListEl.appendChild(li);
  });
}


/**
 * Loads a specific chat into the main message view.
 * @param {string} chatId - The ID of the chat to load.
 */
function loadChat(chatId) {
  // Clear current messages.
  messagesEl.innerHTML = "";

  const chat = chats.find(c => c.id === chatId);
  if (!chat) return; // Exit if chat not found

  // Render all messages in history.
  chat.messages.forEach(msg => {
    addMessage(msg.text, msg.sender);
  });
}

// =====================================
// MESSAGE HELPERS
// =====================================

/**
 * Appends a message to the chat window.
 * @param {string} text - The message content.
 * @param {string} sender - 'user' or 'bot'.
 */
function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.textContent = text;
  messagesEl.appendChild(msg);

  // Auto-scroll to the bottom to show new message.
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// =====================================
// SEND MESSAGE LOGIC
// =====================================

/**
 * Handles sending a message to the backend.
 * Updates UI, saves state, and processes the response.
 */
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return; // Ignore empty messages

  const chat = chats.find(c => c.id === activeChatId);
  if (!chat) return;

  // 1. Add User Message to UI and State
  chat.messages.push({ sender: "user", text });
  addMessage(text, "user");
  inputEl.value = ""; // Clear input

  // 2. Update Chat Title if it's the first message
  if (chat.title === "New Chat") {
    chat.title = text.slice(0, 30); // Use first 30 chars as title
  }

  renderSidebar();
  saveState();

  // 3. Show Typing Indicator
  const typing = document.createElement("div");
  typing.className = "message bot";
  typing.textContent = "Typing...";
  messagesEl.appendChild(typing);

  try {
    // 4. Send Request to API
    const res = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, region: REGION })
    });

    const data = await res.json();

    // 5. Remove Typing Indicator
    typing.remove();

    // 6. Add Bot Response to UI and State
    chat.messages.push({ sender: "bot", text: data.reply });
    addMessage(data.reply, "bot");
    saveState();

  } catch (err) {
    // Handle Errors
    typing.remove();
    addMessage("Server error. Please try again.", "bot");
    console.error("Chat Error:", err);
  }
}

// =====================================
// EVENT HANDLERS
// =====================================

/**
 * Handles the Enter key press in the input field.
 * Triggers sendMessage().
 */
function handleEnter(e) {
  if (e.key === "Enter") sendMessage();
}

// =====================================
// THEME HANDLING
// =====================================

/**
 * Toggles between light and dark themes.
 * Persists preference to local storage.
 */
function toggleTheme() {
  const html = document.documentElement;
  const next = html.dataset.theme === "dark" ? "light" : "dark";
  html.dataset.theme = next;
  localStorage.setItem("theme", next);
}

// Immediately Invoked Function Expression (IIFE) to apply saved theme on load.
(function () {
  const saved = localStorage.getItem("theme");
  if (saved) document.documentElement.dataset.theme = saved;
})();

// =====================================
// DATA STORAGE
// =====================================

/**
 * Saves the current chat state (list and active ID) to localStorage.
 */
function saveState() {
  localStorage.setItem("chats", JSON.stringify(chats));
  localStorage.setItem("activeChatId", activeChatId);
}

/**
 * Deletes a chat by ID.
 * Updates selection if the active chat is deleted.
 * @param {string} chatId - ID to delete.
 */
function deleteChat(chatId) {
  const index = chats.findIndex(c => c.id === chatId);
  if (index === -1) return;

  // Remove from array.
  chats.splice(index, 1);

  // If we deleted the active chat, switch to another one or create new.
  if (activeChatId === chatId) {
    activeChatId = chats.length ? chats[0].id : null;
    if (activeChatId) loadChat(activeChatId);
    else createNewChat();
  }

  saveState();
  renderSidebar();
}
