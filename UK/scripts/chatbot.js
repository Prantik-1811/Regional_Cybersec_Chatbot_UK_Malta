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

let chatbotOpen = false;

/**
 * Toggles the visibility of the chatbot window.
 * Handles focus management for accessibility.
 */
function toggleChatbot() {
    const container = document.querySelector('.chatbot-container');
    chatbotOpen = !chatbotOpen;

    if (chatbotOpen) {
        container.classList.remove('hidden');
        container.classList.add('open');
        // Auto-focus input when opened
        document.getElementById('chat-input').focus();
    } else {
        container.classList.add('hidden');
        container.classList.remove('open');
    }
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
