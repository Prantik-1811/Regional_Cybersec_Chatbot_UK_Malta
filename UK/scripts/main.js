/**
 * UK Cybersecurity Website - Main JavaScript
 * 
 * This file orchestrates the core functionality of the website, including:
 * - SPA-like Navigation (switching tabs)
 * - Theme Management (Dark/Light mode)
 * - fetching and displaying news articles
 * - Animated Counters
 * - Live Threat Map Simulation
 * - Crime Reporting Form Logic
 */

// =========================================================
// GLOBAL STATE MANAGEMENT
// =========================================================
const state = {
  currentTab: 'home',       // Currently active tab
  articles: [],             // All loaded articles
  filteredArticles: [],     // Articles currently visible after filtering
  visibleCount: 9,          // Pagination limit
  currentFilter: 'all',     // Current category filter
  theme: localStorage.getItem('theme') || 'dark' // Persisted theme preference
};

// =========================================================
// INITIALIZATION
// =========================================================
// Hook into DOMContentLoaded to start the application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  loadArticles(); // Fetch news
  initCounters(); // Start number animations
  initAttackMap(); // Prepare map stats
  initReportForm(); // Reset form state
});

// =========================================================
// THEME MODULE
// =========================================================

/**
 * Applies the saved theme on startup.
 */
function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

/**
 * Toggles between light and dark modes.
 * Saves preference to localStorage.
 */
function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('theme', state.theme);
  updateThemeIcon();
}

/**
 * Updates the theme toggle button icon based on current state.
 */
function updateThemeIcon() {
  const btn = document.querySelector('.theme-toggle');
  if (btn) {
    btn.innerHTML = state.theme === 'dark' ? '☀️' : '🌙';
  }
}

// =========================================================
// NAVIGATION MODULE
// =========================================================

/**
 * Sets up event listeners for navigation tabs.
 */
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Ignore external links (like API docs) that reuse the nav-tab class
      if (!tab.dataset.tab) return;

      const tabId = tab.dataset.tab;
      switchTab(tabId);
    });
  });
}

/**
 * Switches the active view (tab).
 * Handles visibility toggling and specific initialization for certain tabs.
 * @param {string} tabId - The ID of the section to show.
 */
function switchTab(tabId) {
  // Update nav tabs visual state
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabId);
  });

  // Show/Hide content sections
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === tabId);
  });

  state.currentTab = tabId;

  // Specific Actions per Tab:
  // 1. Re-trigger counter animation if switching to home
  if (tabId === 'home') {
    initCounters();
  }

  // 2. Restart map simulation if switching to threats
  if (tabId === 'threats') {
    startAttackSimulation();
  }
}

// =========================================================
// ARTICLE FEED MODULE
// =========================================================

/**
 * Fetches articles from the backend API.
 * Uses a fallback dataset if the API is offline.
 */
async function loadArticles() {
  try {
    const response = await fetch('http://localhost:8001/api/articles?limit=50');
    const data = await response.json();

    // Normalize data structure (handle array or object wrapper)
    const rawArticles = data.articles || (Array.isArray(data) ? data : []);

    // Process and enrich article data
    state.articles = processArticles(rawArticles);
    state.filteredArticles = [...state.articles]; // Initial filter is 'all'

    renderCategoryFilters();
    renderArticleGrid();
  } catch (error) {
    console.error('Error loading articles:', error);
    // Use dummy data if backend fails/offline
    renderFallbackGrid();
  }
}

/**
 * Processes raw API data into usable article objects.
 * Handles deduplication, default titles, and categorization.
 */
function processArticles(data) {
  const articles = [];
  const seenUrls = new Set();

  data.forEach(item => {
    // Basic validation
    const content = item.full_content || item.content || '';
    if (!item.url || seenUrls.has(item.url) || !content) return;

    seenUrls.add(item.url);

    // Clean up Title
    let title = item.title || '';
    if (!title || title === 'Unknown' || title === item.url) {
      // Fallback: Generate title from URL slug if missing
      const parts = item.url.split('/').filter(p => p);
      title = (parts[parts.length - 1] || 'Cyber Security')
        .replace(/-/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    }

    // Determine Category and Icon
    const category = item.category || getCategoryFromUrl(item.url);
    const excerpt = item.excerpt || content.substring(0, 200) + '...';
    const icon = getCategoryIcon(category);

    articles.push({ title, excerpt, url: item.url, icon, category, full_content: content });
  });

  return articles;
}

/**
 * Heuristic function to guess category from URL keywords.
 */
function getCategoryFromUrl(url) {
  const u = url.toLowerCase();
  if (u.includes('physical')) return 'Physical Security';
  if (u.includes('technical')) return 'Technical Security';
  if (u.includes('human')) return 'Human Security';
  if (u.includes('iot') || u.includes('internet-of-things')) return 'IoT Security';
  if (u.includes('threat')) return 'Threat Intelligence';
  if (u.includes('career')) return 'Careers';
  if (u.includes('social-engineering') || u.includes('scam')) return 'Social Engineering';
  if (u.includes('hacker') || u.includes('nation-state')) return 'Threat Actors';
  if (u.includes('attack') || u.includes('supply-chain')) return 'Attack Vectors';
  if (u.includes('vulnerabilit')) return 'Vulnerabilities';
  if (u.includes('cryptograph') || u.includes('quantum')) return 'Cryptography';
  if (u.includes('governance') || u.includes('protection')) return 'Governance';
  return 'Cyber Security';
}

/**
 * Returns an emoji icon based on the category name.
 */
function getCategoryIcon(category) {
  const icons = {
    'Physical Security': '🏢', 'Technical Security': '💻', 'Human Security': '👥',
    'IoT Security': '📱', 'Threat Intelligence': '⚠️', 'Careers': '💼',
    'Social Engineering': '🎭', 'Threat Actors': '🕵️', 'Attack Vectors': '🎯',
    'Vulnerabilities': '🛡️', 'Cryptography': '🔐', 'Governance': '📋',
    'Malware': '🦠', 'Cyber Security': '🔒'
  };
  return icons[category] || '🔒';
}

/**
 * Renders the category filter buttons dynamically based on available articles.
 */
function renderCategoryFilters() {
  const filterBar = document.getElementById('category-filter');
  if (!filterBar) return;

  // Extract unique categories
  const categories = [...new Set(state.articles.map(a => a.category))];

  // Create buttons
  filterBar.innerHTML =
    `<button class="filter-btn active" onclick="filterArticles('all')">All (${state.articles.length})</button>` +
    categories.map(cat => {
      const count = state.articles.filter(a => a.category === cat).length;
      return `<button class="filter-btn" onclick="filterArticles('${cat}')">${getCategoryIcon(cat)} ${cat} (${count})</button>`;
    }).join('');
}

/**
 * Filters the displayed articles by category.
 * @param {string} category - Category name or 'all'.
 */
function filterArticles(category) {
  state.currentFilter = category;
  state.visibleCount = 9; // Reset pagination

  if (category === 'all') {
    state.filteredArticles = [...state.articles];
  } else {
    state.filteredArticles = state.articles.filter(a => a.category === category);
  }

  // Update visual state of filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    const isAll = category === 'all' && btn.textContent.startsWith('All');
    const isMatch = !isAll && btn.textContent.includes(category);
    btn.classList.toggle('active', isAll || isMatch);
  });

  renderArticleGrid();
}

/**
 * Renders the valid articles into the grid container.
 * Handles "Load More" functionality and empty states.
 */
function renderArticleGrid() {
  const grid = document.getElementById('article-grid');
  const loadMoreContainer = document.getElementById('load-more-container');
  if (!grid) return;

  // Slice for pagination
  const visible = state.filteredArticles.slice(0, state.visibleCount);

  // Empty State
  if (visible.length === 0) {
    grid.innerHTML = '<div class="no-articles"><p>🔍 No articles found for this category.</p></div>';
    if (loadMoreContainer) loadMoreContainer.style.display = 'none';
    return;
  }

  // Map articles to HTML cards
  grid.innerHTML = visible.map((article, idx) => {
    const originalIndex = state.articles.indexOf(article);
    // First card can be styled as a "Hero" card
    const isHero = idx === 0;

    // Extract hostname for display
    let hostname = '';
    try { hostname = new URL(article.url).hostname; } catch (e) { hostname = 'source'; }

    return `
      <div class="article-card-grid ${isHero ? 'hero-card' : ''}" onclick="openArticle(${originalIndex})">
        <div class="card-icon-area">
          <span class="card-icon">${article.icon}</span>
          <span class="card-category">${article.category}</span>
        </div>
        <div class="card-body">
          <h3 class="card-title">${article.title}</h3>
          <p class="card-excerpt">${article.excerpt}</p>
        </div>
        <div class="card-footer">
          <span class="card-source">${hostname}</span>
          <span class="card-read-btn">Read Article →</span>
        </div>
      </div>
    `;
  }).join('');

  // Update "Load More" button visibility
  if (loadMoreContainer) {
    loadMoreContainer.style.display = state.filteredArticles.length > state.visibleCount ? 'flex' : 'none';
  }
}

/**
 * Increases the visible count of articles.
 */
function loadMoreArticles() {
  state.visibleCount += 9;
  renderArticleGrid();
}

/**
 * Provides hardcoded sample data when backend is unreachable.
 */
function renderFallbackGrid() {
  state.articles = [
    { title: 'Areas of Cyber Security', excerpt: 'Cyber security is made up of three main areas - physical, technical and human.', icon: '🔒', category: 'Cyber Security', url: 'https://cyber.uk', full_content: 'Cyber security is made up of three main areas - physical, technical and human. Understanding all three is essential.' },
    { title: 'Physical Cyber Security', excerpt: 'Physical security continues to be crucial to cyber information safety.', icon: '🏢', category: 'Physical Security', url: 'https://cyber.uk/physical', full_content: 'Physical security has been important long before cyber security.' },
    { title: 'Technical Cyber Security', excerpt: 'Technical security covers antivirus, ethical hacking, and vulnerability assessments.', icon: '💻', category: 'Technical Security', url: 'https://cyber.uk/technical', full_content: 'Technical cyber security involves protecting ourselves digitally.' },
    { title: 'Human Cyber Security', excerpt: 'People play a crucial role in their own cyber security.', icon: '👥', category: 'Human Security', url: 'https://cyber.uk/human', full_content: 'Awareness-raising is key to the human side of security.' }
  ];
  state.filteredArticles = [...state.articles];
  renderCategoryFilters();
  renderArticleGrid();
}

// =========================================================
// ARTICLE READER (IN-PLACE)
// =========================================================

/**
 * Opens an article in the dedicated reader view.
 * Splits text into paragraphs for better readability.
 * @param {number} index - Index of the article in the global state array.
 */
function openArticle(index) {
  const article = state.articles[index];
  if (!article) return;

  const feedView = document.getElementById('news-feed');
  const readerView = document.getElementById('article-viewer');

  // Populate header data
  document.getElementById('viewer-tag').textContent = article.category;
  document.getElementById('viewer-title').textContent = article.title;

  // Source domain label
  try {
    document.getElementById('viewer-source').textContent = new URL(article.url).hostname;
  } catch (e) {
    document.getElementById('viewer-source').textContent = 'Source';
  }

  // Format content: Split sentences to create paragraphs roughly every 3 sentences
  const rawContent = article.full_content || article.excerpt;
  const sentences = rawContent.split(/(?<=\.)\s+/);
  const paragraphs = [];
  let currentParagraph = [];

  sentences.forEach((sentence, i) => {
    currentParagraph.push(sentence);
    // Bundle 3 sentences or flush on last one
    if (currentParagraph.length >= 3 || i === sentences.length - 1) {
      paragraphs.push(currentParagraph.join(' '));
      currentParagraph = [];
    }
  });

  // Inject formatted paragraphs
  document.getElementById('viewer-content').innerHTML = paragraphs.map(p => `<p>${p}</p>`).join('');

  // Set the ACTUAL external source URL button
  const viewerLink = document.getElementById('viewer-link');
  viewerLink.href = article.url;
  viewerLink.setAttribute('target', '_blank');
  viewerLink.setAttribute('rel', 'noopener noreferrer');

  // Render suggested "Related" articles
  renderSuggestedArticles(index);

  // Switch views (Hide grid, Show reader)
  feedView.classList.add('hidden');
  readerView.classList.remove('hidden');

  // Auto-scroll to top of section for better UX
  const section = document.getElementById('insights');
  if (section) section.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Finds and displays related articles in the reader footer.
 */
function renderSuggestedArticles(currentIndex) {
  const container = document.getElementById('suggested-articles');
  if (!container) return;

  const current = state.articles[currentIndex];
  // Create list of other articles with their original indices
  let related = state.articles
    .map((a, i) => ({ ...a, _idx: i }))
    .filter(a => a._idx !== currentIndex);

  // Sort: prioritize same-category articles
  related.sort((a, b) => {
    const aMatch = a.category === current.category ? 0 : 1;
    const bMatch = b.category === current.category ? 0 : 1;
    return aMatch - bMatch;
  });

  // Take top 3
  const suggestions = related.slice(0, 3);

  container.innerHTML = suggestions.map(article => `
    <div class="suggested-card glass-card" onclick="openArticle(${article._idx})">
      <span class="card-icon-small">${article.icon}</span>
      <div class="suggested-info">
        <span class="card-category-small">${article.category}</span>
        <h4 class="suggested-card-title">${article.title}</h4>
      </div>
    </div>
  `).join('');
}

/**
 * Closes the article reader and returns to the feed.
 */
function closeArticle() {
  const feedView = document.getElementById('news-feed');
  const readerView = document.getElementById('article-viewer');

  readerView.classList.add('hidden');
  feedView.classList.remove('hidden');

  // Scroll back to feed top
  const section = document.getElementById('insights');
  if (section) section.scrollIntoView({ behavior: 'smooth' });
}

// =========================================================
// ANIMATED COUNTERS MODULE
// =========================================================

/**
 * Initializes and triggers number counting animations when scrolled into view.
 */
function initCounters() {
  const counters = document.querySelectorAll('[data-counter]');

  counters.forEach(counter => {
    const target = parseInt(counter.dataset.counter);
    const duration = 2000; // 2 seconds animation
    const step = target / (duration / 16); // ~60fps
    let current = 0;

    counter.textContent = '0';

    const updateCounter = () => {
      current += step;
      if (current < target) {
        counter.textContent = formatNumber(Math.floor(current));
        requestAnimationFrame(updateCounter);
      } else {
        counter.textContent = formatNumber(target);
      }
    };

    // Use IntersectionObserver to start animation only when visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          updateCounter();
          observer.unobserve(entry.target); // Run once
        }
      });
    }, { threshold: 0.5 });

    observer.observe(counter);
  });
}

/**
 * Formats numbers with locale separators (e.g., 1,000,000).
 */
function formatNumber(num) {
  return num.toLocaleString('en-GB');
}

// =========================================================
// LIVE ATTACK MAP SIMULATION
// =========================================================
// Predefined coordinates for map visualizations
const attackCountries = [
  { name: 'Russia', code: 'RU', x: 75, y: 25 },
  { name: 'China', code: 'CN', x: 82, y: 40 },
  { name: 'USA', code: 'US', x: 20, y: 35 },
  { name: 'North Korea', code: 'KP', x: 85, y: 35 },
  { name: 'Iran', code: 'IR', x: 65, y: 40 },
  { name: 'Brazil', code: 'BR', x: 30, y: 65 },
  { name: 'India', code: 'IN', x: 72, y: 45 },
  { name: 'Germany', code: 'DE', x: 52, y: 30 },
  { name: 'UK', code: 'GB', x: 48, y: 28 },
  { name: 'Nigeria', code: 'NG', x: 52, y: 52 }
];

const attackTypes = [
  { name: 'Phishing', color: '#ef4444', count: 0 },
  { name: 'Ransomware', color: '#f59e0b', count: 0 },
  { name: 'DDoS', color: '#8b5cf6', count: 0 },
  { name: 'Malware', color: '#ec4899', count: 0 },
  { name: 'SQL Injection', color: '#14b8a6', count: 0 }
];

let attackStats = {
  total: 0,
  blocked: 0,
  active: 0
};

function initAttackMap() {
  updateThreatStats();
}

/**
 * Starts the interval for random attack generation.
 */
function startAttackSimulation() {
  // Simulate new attacks every 2-4 seconds with randomness
  setInterval(() => {
    simulateAttack();
  }, 2000 + Math.random() * 2000);

  // Trigger a burst of initial attacks
  for (let i = 0; i < 5; i++) {
    setTimeout(() => simulateAttack(), i * 500);
  }
}

/**
 * Generates a random attack event between two countries.
 */
function simulateAttack() {
  const sourceIndex = Math.floor(Math.random() * attackCountries.length);
  const targetIndex = Math.floor(Math.random() * attackCountries.length);

  // Prevent self-attack (unless internal?) - simplify to distinct for visual clarity
  if (sourceIndex === targetIndex) return;

  const source = attackCountries[sourceIndex];
  const target = attackCountries[targetIndex];
  const attackType = attackTypes[Math.floor(Math.random() * attackTypes.length)];

  // Update Stats
  attackStats.total++;
  attackType.count++;

  // 70% chance of being "Blocked" (for positive user feeling)
  if (Math.random() < 0.7) {
    attackStats.blocked++;
  } else {
    attackStats.active++;
    // Active attacks resolve after 5 seconds
    setTimeout(() => attackStats.active--, 5000);
  }

  // Trigger visual lines
  createAttackLine(source, target, attackType.color);
  updateThreatStats();
}

/**
 * Creates and animates a DOM element representing a cyber attack packet.
 */
function createAttackLine(source, target, color) {
  const container = document.querySelector('.attack-lines');
  if (!container) return;

  const line = document.createElement('div');
  line.className = 'attack-animation';
  // CSS variables control the trajectory
  line.style.cssText = `
    position: absolute;
    left: ${source.x}%;
    top: ${source.y}%;
    width: 10px;
    height: 10px;
    background: ${color};
    border-radius: 50%;
    box-shadow: 0 0 10px ${color}, 0 0 20px ${color};
    animation: attackMove 1.5s ease-in-out forwards;
    --targetX: ${target.x - source.x}%;
    --targetY: ${target.y - source.y}%;
  `;

  container.appendChild(line);

  // Cleanup DOM after animation finishes
  setTimeout(() => line.remove(), 1500);
}

/**
 * Updates the statistical display on the threat map.
 */
function updateThreatStats() {
  const elements = {
    total: document.querySelector('[data-stat="total"]'),
    blocked: document.querySelector('[data-stat="blocked"]'),
    active: document.querySelector('[data-stat="active"]')
  };

  if (elements.total) elements.total.textContent = formatNumber(attackStats.total);
  if (elements.blocked) elements.blocked.textContent = formatNumber(attackStats.blocked);
  if (elements.active) elements.active.textContent = attackStats.active;

  // Update list of attack types/counts
  const typeList = document.querySelector('.threat-type-list');
  if (typeList) {
    typeList.innerHTML = attackTypes.map(type => `
      <div class="threat-type-item">
        <span class="threat-type-name">
          <span class="threat-type-dot" style="background: ${type.color}"></span>
          ${type.name}
        </span>
        <span class="threat-type-count">${type.count}</span>
      </div>
    `).join('');
  }
}

// =========================================================
// CRIME REPORT FORM MODULE
// =========================================================
let currentFormStep = 1;
let selectedCategory = null;

function initReportForm() {
  updateFormProgress();
}

/**
 * Handles category selection in step 1 of the form.
 */
function selectCategory(element, category) {
  // Clear previous selection
  document.querySelectorAll('.category-option').forEach(opt => {
    opt.classList.remove('selected');
  });

  // Apply new selection
  element.classList.add('selected');
  selectedCategory = category;
}

/**
 * Advances to the next form step with validation.
 */
function nextFormStep() {
  // Validation for Step 1
  if (currentFormStep === 1 && !selectedCategory) {
    alert('Please select a crime category');
    return;
  }

  if (currentFormStep < 3) {
    currentFormStep++;
    updateFormProgress();
    showFormStep(currentFormStep);
  }
}

/**
 * Returns to the previous form step.
 */
function prevFormStep() {
  if (currentFormStep > 1) {
    currentFormStep--;
    updateFormProgress();
    showFormStep(currentFormStep);
  }
}

/**
 * Updates the visual progress bar.
 */
function updateFormProgress() {
  const steps = document.querySelectorAll('.progress-step');
  steps.forEach((step, index) => {
    step.classList.remove('active', 'completed');
    if (index + 1 === currentFormStep) {
      step.classList.add('active');
    } else if (index + 1 < currentFormStep) {
      step.classList.add('completed');
    }
  });
}

/**
 * Toggles visibility of form sections based on current step.
 */
function showFormStep(step) {
  document.querySelectorAll('.form-section').forEach((section, index) => {
    section.classList.toggle('active', index + 1 === step);
  });
}

/**
 * Handles form submission.
 * Validates data and shows success message.
 */
function submitReport(event) {
  event.preventDefault();

  // In a real app, we would gather form data and POST to backend here.
  // const formData = new FormData(event.target);

  // Show success message replacement
  const form = document.querySelector('.report-form');
  form.innerHTML = `
    <div style="text-align: center; padding: 3rem;">
      <div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
      <h2 style="margin-bottom: 1rem;">Report Submitted Successfully</h2>
      <p style="color: var(--text-secondary); margin-bottom: 2rem;">
        Your cybercrime report has been submitted. A reference number will be sent to your email.
        <br><br>
        For urgent matters, please contact Action Fraud directly at <strong>0300 123 2040</strong>
      </p>
      <button class="btn btn-primary" onclick="location.reload()">Submit Another Report</button>
    </div>
  `;
}

// =========================================================
// UTILITY FUNCTIONS
// =========================================================

/**
 * Debounce function to limit rate of execution (e.g., for resize events).
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// =========================================================
// EXPORTS
// =========================================================
// Expose functions to global scope for HTML onclick handlers to work.
window.toggleTheme = toggleTheme;
window.switchTab = switchTab;
// window.nextSlide = nextSlide; // Removed if unused
// window.prevSlide = prevSlide; // Removed if unused
// window.goToSlide = goToSlide; // Removed if unused
window.selectCategory = selectCategory;
window.nextFormStep = nextFormStep;
window.prevFormStep = prevFormStep;
window.submitReport = submitReport;
