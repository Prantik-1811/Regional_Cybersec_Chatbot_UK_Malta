/**
 * CyberSafe UK - Chatbot and Update Checker Frontend
 * 
 * This script manages two main features:
 * 1. The floating chatbot widget that interacts with the backend AI.
 * 2. The auto-update notification banner that checks for new content.
 */

const API_BASE = 'http://localhost:8001/api';

// ============================================
// UPDATE CHECKER MODULE
// ============================================

/**
 * Checks the backend for new content updates.
 * Displays a notification banner if new articles or sources are available.
 */
async function checkForUpdates() {
  const banner = document.getElementById('update-banner');
  const textEl = banner.querySelector('.update-text');

  try {
    // Show banner with loading state
    banner.classList.remove('hidden');
    textEl.textContent = 'Checking for updates...';

    // Fetch update status from the API
    const response = await fetch(`${API_BASE}/updates?limit=5`);

    if (!response.ok) {
      throw new Error('Backend not available');
    }

    const data = await response.json();

    // Check if there are any updates marked as having new content
    if (data.updates && data.updates.length > 0) {
      const newUpdates = data.updates.filter(u => u.has_new_content);

      if (newUpdates.length > 0) {
        // Formatting: Show count of sources with updates
        textEl.textContent = `🔔 ${newUpdates.length} source(s) have new content!`;
        banner.classList.add('has-updates');
      } else {
        // No new content found
        textEl.textContent = `✓ All ${data.total_sources} sources are up to date`;
        // Auto-hide after 3 seconds
        setTimeout(() => closeBanner(), 3000);
      }
    } else {
      // Fallback if update list is empty but request succeeded
      textEl.textContent = '✓ Sources checked, no new updates';
      setTimeout(() => closeBanner(), 3000);
    }
  } catch (error) {
    // Handle offline or error states
    console.log('Update checker: Backend not available');
    textEl.textContent = '⚠️ Backend offline - Start server for live updates';
    setTimeout(() => closeBanner(), 5000);
  }
}

/**
 * Hides the update notification banner.
 */
function closeBanner() {
  const banner = document.getElementById('update-banner');
  banner.classList.add('hidden');
}

// ============================================
// CHATBOT MODULE
// ============================================

/** @type {boolean} Whether the chatbot panel is currently visible */
let chatbotOpen = false;
/** @type {boolean} Whether the chatbot is in fullscreen overlay mode */
let chatbotFullscreen = false;

/**
 * Toggles the visibility of the chatbot panel.
 * - On open: removes 'hidden', adds 'open', and auto-focuses the input field.
 * - On close: reverses the above and also exits fullscreen mode if active.
 */
function toggleChatbot() {
  const container = document.querySelector('.chatbot-container');
  chatbotOpen = !chatbotOpen;

  if (chatbotOpen) {
    container.classList.remove('hidden');
    container.classList.add('open');
    // Auto-focus the text input for immediate typing
    document.getElementById('chat-input').focus();
  } else {
    container.classList.add('hidden');
    container.classList.remove('open');
    // Automatically exit fullscreen when closing the chatbot
    if (chatbotFullscreen) {
      chatbotFullscreen = false;
      document.querySelector('.chatbot-widget').classList.remove('chatbot-fullscreen');
    }
  }
}

/**
 * Toggles the chatbot between its normal floating position (bottom-right)
 * and a fullscreen overlay that covers the entire viewport.
 * Adds/removes the 'chatbot-fullscreen' class on the widget wrapper.
 */
function toggleChatFullscreen() {
  chatbotFullscreen = !chatbotFullscreen;
  const widget = document.querySelector('.chatbot-widget');
  widget.classList.toggle('chatbot-fullscreen', chatbotFullscreen);
}

/**
 * Opens the current chatbot conversation in a new browser tab as a standalone page.
 *
 * How it works:
 * 1. Copies the current chat message HTML from #chatbot-messages.
 * 2. Builds a complete standalone HTML page (with inline CSS + JS) that:
 *    - Renders the existing messages in a dark-themed layout.
 *    - Provides a working input + Send button connected to the same API_BASE.
 * 3. Creates a Blob URL from the HTML string and opens it in a new tab.
 *
 * NOTE: The pop-out tab is self-contained. Subsequent messages sent in the
 * pop-out tab are NOT synced back to the original chatbot widget.
 */
function popoutChatbot() {
  // Capture all current chat messages as raw HTML
  const messages = document.getElementById('chatbot-messages').innerHTML;
  const popupHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CyberSafe AI — Chat</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
      background: #0a0e1a;
      color: #e2e8f0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: linear-gradient(135deg, #0ea5e9, #6366f1);
      color: white;
      padding: 1rem 1.5rem;
      font-weight: 700;
      font-size: 1.15rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .chat-message { max-width: 85%; padding: 0.85rem 1.1rem; border-radius: 16px; line-height: 1.55; font-size: 0.95rem; }
    .chat-message.user { align-self: flex-end; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; border-bottom-right-radius: 4px; }
    .chat-message.bot { align-self: flex-start; background: rgba(30,41,59,0.8); border: 1px solid rgba(100,116,139,0.25); border-bottom-left-radius: 4px; }
    .chat-message p { margin: 0; }
    .input-area {
      padding: 1rem 1.5rem;
      background: rgba(15,23,42,0.9);
      border-top: 1px solid rgba(100,116,139,0.2);
      display: flex;
      gap: 0.75rem;
    }
    .input-area input {
      flex: 1;
      padding: 0.8rem 1rem;
      background: rgba(30,41,59,0.6);
      border: 1px solid rgba(100,116,139,0.3);
      border-radius: 12px;
      color: #e2e8f0;
      font-size: 0.95rem;
      outline: none;
    }
    .input-area input:focus { border-color: #0ea5e9; }
    .input-area button {
      padding: 0.8rem 1.5rem;
      background: linear-gradient(135deg, #0ea5e9, #6366f1);
      color: white;
      border: none;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, opacity 0.2s;
    }
    .input-area button:hover { transform: scale(1.04); }
    .sources { margin-top: 0.5rem; font-size: 0.8rem; }
    .sources a { color: #38bdf8; text-decoration: none; margin-right: 0.5rem; }
    .sources a:hover { text-decoration: underline; }
    .sources-label { color: #94a3b8; margin-right: 0.25rem; }
    sup.citation { color: #38bdf8; font-size: 0.7rem; }
    code { background: rgba(0,0,0,0.3); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85rem; }
    .dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#64748b; margin:0 2px; animation: dotPulse 1.4s infinite ease-in-out both; }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotPulse { 0%,80%,100%{transform:scale(0)}40%{transform:scale(1)} }
  </style>
</head>
<body>
  <header>🤖 CyberSafe AI</header>
  <div class="messages" id="chatbot-messages">${messages}</div>
  <div class="input-area">
    <input type="text" id="chat-input" placeholder="Ask about cybersecurity..." autofocus>
    <button id="send-btn">Send</button>
  </div>
  <script>
    const API_BASE = '${API_BASE}';
    const input = document.getElementById('chat-input');
    const btn = document.getElementById('send-btn');
    const container = document.getElementById('chatbot-messages');

    function addMsg(text, type, sources) {
      const d = document.createElement('div');
      d.className = 'chat-message ' + type;
      let html = '<p>' + text
        .replace(/\\[(\\d+)\\]/g, '<sup class="citation">[$1]</sup>')
        .replace(/\`\`\`([^\`]+)\`\`\`/g, '<code>$1</code>')
        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\n/g, '<br>') + '</p>';
      if (sources && sources.length) {
        html += '<div class="sources"><span class="sources-label">Sources:</span>';
        sources.forEach(function(s,i){html+='<a href="'+s.url+'" target="_blank">[' +(i+1)+'] '+s.title+'</a>';});
        html += '</div>';
      }
      d.innerHTML = html;
      container.appendChild(d);
      container.scrollTop = container.scrollHeight;
    }

    async function send() {
      const msg = input.value.trim();
      if (!msg) return;
      addMsg(msg, 'user');
      input.value = '';
      const dots = document.createElement('div');
      dots.className = 'chat-message bot typing';
      dots.id = 'typing';
      dots.innerHTML = '<p><span class="dot"></span><span class="dot"></span><span class="dot"></span></p>';
      container.appendChild(dots);
      container.scrollTop = container.scrollHeight;
      try {
        const res = await fetch(API_BASE + '/query', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:msg,region:'UK'}) });
        const el = document.getElementById('typing'); if(el) el.remove();
        if (!res.ok) throw new Error();
        const data = await res.json();
        addMsg(data.answer, 'bot', data.sources);
      } catch(e) {
        const el = document.getElementById('typing'); if(el) el.remove();
        addMsg("I'm currently offline. Please start the backend server.", 'bot');
      }
    }

    btn.addEventListener('click', send);
    input.addEventListener('keypress', function(e){ if(e.key==='Enter') send(); });
  </script>
</body>
</html>`;
  const blob = new Blob([popupHtml], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank');
}

/**
 * Handles the 'Enter' key press in the chat input.
 * Triggers the message sending function.
 */
function handleChatKeypress(event) {
  if (event.key === 'Enter') {
    sendChatMessage();
  }
}

/**
 * Sends the user's message to the backend API and displays the response.
 */
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();

  // Prevent sending empty messages
  if (!message) return;

  const messagesContainer = document.getElementById('chatbot-messages');

  // 1. Display User Message
  addChatMessage(message, 'user');
  input.value = ''; // Clear input field

  // 2. Show Typing Indicator
  const typingId = addTypingIndicator();

  try {
    // 3. Send Request to API
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: message,
        region: 'UK' // Context is fixed to UK for this frontend
      })
    });

    // 4. Remove Typing Indicator once response is received
    removeTypingIndicator(typingId);

    if (!response.ok) {
      throw new Error('Backend not available');
    }

    const data = await response.json();

    // 5. Display Bot Response with Sources
    addChatMessage(data.answer, 'bot', data.sources);

  } catch (error) {
    // Handle Errors (e.g., backend offline)
    removeTypingIndicator(typingId);

    // Display a helpful offline message with instructions
    addChatMessage(
      "I'm currently offline. Please start the backend server:\n\n" +
      "```\ncd UK/backend\npython main.py\n```\n\n" +
      "In the meantime, visit [Action Fraud](https://www.actionfraud.police.uk) or " +
      "[NCSC](https://www.ncsc.gov.uk) for official guidance.",
      'bot'
    );
  }
}

/**
 * Appends a message bubble to the chat window.
 * Supports Markdown-like formatting and citation sources.
 * 
 * @param {string} text - The message content.
 * @param {string} type - 'user' or 'bot'.
 * @param {Array} sources - Optional list of source objects {url, title} used for the answer.
 */
function addChatMessage(text, type, sources = []) {
  const container = document.getElementById('chatbot-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${type}`;

  // Simple Markdown parsing for better readability
  let formattedText = text
    .replace(/\[(\d+)\]/g, '<sup class="citation">[$1]</sup>') // Citation numbers [1] -> <sup>[1]</sup>
    .replace(/```([^`]+)```/g, '<code>$1</code>') // Code blocks
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>') // Bold text
    .replace(/\n/g, '<br>'); // Line breaks

  let html = `<p>${formattedText}</p>`;

  // Append sources list if available
  if (sources && sources.length > 0) {
    html += '<div class="sources">';
    html += '<span class="sources-label">Sources:</span>';
    sources.forEach((source, i) => {
      html += `<a href="${source.url}" target="_blank" class="source-link">[${i + 1}] ${source.title}</a>`;
    });
    html += '</div>';
  }

  messageDiv.innerHTML = html;
  container.appendChild(messageDiv);

  // Auto-scroll to the bottom
  container.scrollTop = container.scrollHeight;
}

/**
 * Adds a visual typing indicator to the chat.
 * @returns {string} ID of the indicator element to allow removal later.
 */
function addTypingIndicator() {
  const container = document.getElementById('chatbot-messages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-message bot typing';
  typingDiv.id = 'typing-indicator';
  // Three dots animation
  typingDiv.innerHTML = '<p><span class="dot"></span><span class="dot"></span><span class="dot"></span></p>';
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
  return 'typing-indicator';
}

/**
 * Removes the typing indicator from the DOM.
 * @param {string} id - The ID of the indicator element.
 */
function removeTypingIndicator(id) {
  const indicator = document.getElementById(id);
  if (indicator) {
    indicator.remove();
  }
}

// ============================================
// INITIALIZATION
// ============================================

// Check for updates shortly after page load.
// The delay ensures the UI is fully rendered and doesn't impact initial TTI.
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(checkForUpdates, 2000);
});
