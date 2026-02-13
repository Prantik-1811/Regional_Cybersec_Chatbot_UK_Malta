/**
 * CyberSafe UK - Chatbot and Update Checker Frontend
 * Connects to the Python backend for AI-powered chat and update notifications
 */

const API_BASE = 'http://localhost:8001/api';

// ============================================
// UPDATE CHECKER
// ============================================

async function checkForUpdates() {
    const banner = document.getElementById('update-banner');
    const textEl = banner.querySelector('.update-text');

    try {
        banner.classList.remove('hidden');
        textEl.textContent = 'Checking for updates...';

        const response = await fetch(`${API_BASE}/updates?limit=5`);

        if (!response.ok) {
            throw new Error('Backend not available');
        }

        const data = await response.json();

        if (data.updates && data.updates.length > 0) {
            const newUpdates = data.updates.filter(u => u.has_new_content);
            if (newUpdates.length > 0) {
                textEl.textContent = `🔔 ${newUpdates.length} source(s) have new content!`;
                banner.classList.add('has-updates');
            } else {
                textEl.textContent = `✓ All ${data.total_sources} sources are up to date`;
                setTimeout(() => closeBanner(), 3000);
            }
        } else {
            textEl.textContent = '✓ Sources checked, no new updates';
            setTimeout(() => closeBanner(), 3000);
        }
    } catch (error) {
        console.log('Update checker: Backend not available');
        textEl.textContent = '⚠️ Backend offline - Start server for live updates';
        setTimeout(() => closeBanner(), 5000);
    }
}

function closeBanner() {
    const banner = document.getElementById('update-banner');
    banner.classList.add('hidden');
}

// ============================================
// CHATBOT
// ============================================

let chatbotOpen = false;

function toggleChatbot() {
    const container = document.querySelector('.chatbot-container');
    chatbotOpen = !chatbotOpen;

    if (chatbotOpen) {
        container.classList.remove('hidden');
        container.classList.add('open');
        document.getElementById('chat-input').focus();
    } else {
        container.classList.add('hidden');
        container.classList.remove('open');
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    const messagesContainer = document.getElementById('chatbot-messages');

    // Add user message
    addChatMessage(message, 'user');
    input.value = '';

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                region: 'UK'
            })
        });

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (!response.ok) {
            throw new Error('Backend not available');
        }

        const data = await response.json();

        // Add bot response
        addChatMessage(data.answer, 'bot', data.sources);

    } catch (error) {
        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add offline message
        addChatMessage(
            "I'm currently offline. Please start the backend server:\n\n" +
            "```\ncd UK/backend\npython main.py\n```\n\n" +
            "In the meantime, visit [Action Fraud](https://www.actionfraud.police.uk) or " +
            "[NCSC](https://www.ncsc.gov.uk) for official guidance.",
            'bot'
        );
    }
}

function addChatMessage(text, type, sources = []) {
    const container = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;

    // Format message with markdown-like styling
    let formattedText = text
        .replace(/\[(\d+)\]/g, '<sup class="citation">[$1]</sup>')
        .replace(/```([^`]+)```/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    let html = `<p>${formattedText}</p>`;

    // Add sources if available
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

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chatbot-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<p><span class="dot"></span><span class="dot"></span><span class="dot"></span></p>';
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

// ============================================
// INITIALIZATION
// ============================================

// Check for updates when page loads (with delay to not block initial render)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(checkForUpdates, 2000);
});
