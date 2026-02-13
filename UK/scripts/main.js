/**
 * UK Cybersecurity Website - Main JavaScript
 * Handles navigation, theme toggle, article slider, counters, and more
 */

// =========================================================
// GLOBAL STATE
// =========================================================
const state = {
  currentTab: 'home',
  articles: [],
  filteredArticles: [],
  visibleCount: 9,
  currentFilter: 'all',
  theme: localStorage.getItem('theme') || 'dark'
};

// =========================================================
// INITIALIZATION
// =========================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  loadArticles();
  initCounters();
  initAttackMap();
  initReportForm();
});

// =========================================================
// THEME TOGGLE
// =========================================================
function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('theme', state.theme);
  updateThemeIcon();
}

function updateThemeIcon() {
  const btn = document.querySelector('.theme-toggle');
  if (btn) {
    btn.innerHTML = state.theme === 'dark' ? '☀️' : '🌙';
  }
}

// =========================================================
// NAVIGATION
// =========================================================
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabId = tab.dataset.tab;
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabId);
  });

  // Update content sections
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === tabId);
  });

  state.currentTab = tabId;

  // Re-trigger counter animation if switching to home
  if (tabId === 'home') {
    initCounters();
  }

  // Re-init map if switching to threats
  if (tabId === 'threats') {
    startAttackSimulation();
  }
}

// =========================================================
// ARTICLE GRID
// =========================================================
async function loadArticles() {
  try {
    const response = await fetch('http://localhost:8001/api/articles?limit=50');
    const data = await response.json();
    const rawArticles = data.articles || (Array.isArray(data) ? data : []);
    state.articles = processArticles(rawArticles);
    state.filteredArticles = [...state.articles];
    renderCategoryFilters();
    renderArticleGrid();
  } catch (error) {
    console.error('Error loading articles:', error);
    renderFallbackGrid();
  }
}

function processArticles(data) {
  const articles = [];
  const seenUrls = new Set();

  data.forEach(item => {
    const content = item.full_content || item.content || '';
    if (!item.url || seenUrls.has(item.url) || !content) return;
    seenUrls.add(item.url);

    let title = item.title || '';
    if (!title || title === 'Unknown' || title === item.url) {
      const parts = item.url.split('/').filter(p => p);
      title = (parts[parts.length - 1] || 'Cyber Security')
        .replace(/-/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    }

    const category = item.category || getCategoryFromUrl(item.url);
    const excerpt = item.excerpt || content.substring(0, 200) + '...';
    const icon = getCategoryIcon(category);

    articles.push({ title, excerpt, url: item.url, icon, category, full_content: content });
  });

  return articles;
}

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

function renderCategoryFilters() {
  const filterBar = document.getElementById('category-filter');
  if (!filterBar) return;

  const categories = [...new Set(state.articles.map(a => a.category))];
  filterBar.innerHTML =
    `<button class="filter-btn active" onclick="filterArticles('all')">All (${state.articles.length})</button>` +
    categories.map(cat => {
      const count = state.articles.filter(a => a.category === cat).length;
      return `<button class="filter-btn" onclick="filterArticles('${cat}')">${getCategoryIcon(cat)} ${cat} (${count})</button>`;
    }).join('');
}

function filterArticles(category) {
  state.currentFilter = category;
  state.visibleCount = 9;

  if (category === 'all') {
    state.filteredArticles = [...state.articles];
  } else {
    state.filteredArticles = state.articles.filter(a => a.category === category);
  }

  // Update active filter button
  document.querySelectorAll('.filter-btn').forEach(btn => {
    const isAll = category === 'all' && btn.textContent.startsWith('All');
    const isMatch = !isAll && btn.textContent.includes(category);
    btn.classList.toggle('active', isAll || isMatch);
  });

  renderArticleGrid();
}

function renderArticleGrid() {
  const grid = document.getElementById('article-grid');
  const loadMoreContainer = document.getElementById('load-more-container');
  if (!grid) return;

  const visible = state.filteredArticles.slice(0, state.visibleCount);

  if (visible.length === 0) {
    grid.innerHTML = '<div class="no-articles"><p>🔍 No articles found for this category.</p></div>';
    if (loadMoreContainer) loadMoreContainer.style.display = 'none';
    return;
  }

  grid.innerHTML = visible.map((article, idx) => {
    const originalIndex = state.articles.indexOf(article);
    const isHero = idx === 0;
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

  if (loadMoreContainer) {
    loadMoreContainer.style.display = state.filteredArticles.length > state.visibleCount ? 'flex' : 'none';
  }
}

function loadMoreArticles() {
  state.visibleCount += 9;
  renderArticleGrid();
}

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

function openArticle(index) {
  const article = state.articles[index];
  if (!article) return;

  const feedView = document.getElementById('news-feed');
  const readerView = document.getElementById('article-viewer');

  // Populate header
  document.getElementById('viewer-tag').textContent = article.category;
  document.getElementById('viewer-title').textContent = article.title;

  // Source domain label
  try {
    document.getElementById('viewer-source').textContent = new URL(article.url).hostname;
  } catch (e) {
    document.getElementById('viewer-source').textContent = 'Source';
  }

  // Format content into readable paragraphs
  const rawContent = article.full_content || article.excerpt;
  const sentences = rawContent.split(/(?<=\.)\s+/);
  const paragraphs = [];
  let currentParagraph = [];

  sentences.forEach((sentence, i) => {
    currentParagraph.push(sentence);
    if (currentParagraph.length >= 3 || i === sentences.length - 1) {
      paragraphs.push(currentParagraph.join(' '));
      currentParagraph = [];
    }
  });

  document.getElementById('viewer-content').innerHTML = paragraphs.map(p => `<p>${p}</p>`).join('');

  // Set the ACTUAL external source URL
  const viewerLink = document.getElementById('viewer-link');
  viewerLink.href = article.url;
  viewerLink.setAttribute('target', '_blank');
  viewerLink.setAttribute('rel', 'noopener noreferrer');

  // Render suggested articles
  renderSuggestedArticles(index);

  // Switch views
  feedView.classList.add('hidden');
  readerView.classList.remove('hidden');

  // Scroll to top of section
  const section = document.getElementById('insights');
  if (section) section.scrollIntoView({ behavior: 'smooth' });
}

function renderSuggestedArticles(currentIndex) {
  const container = document.getElementById('suggested-articles');
  if (!container) return;

  const current = state.articles[currentIndex];
  let related = state.articles
    .map((a, i) => ({ ...a, _idx: i }))
    .filter(a => a._idx !== currentIndex);

  // Sort: same-category articles first
  related.sort((a, b) => {
    const aMatch = a.category === current.category ? 0 : 1;
    const bMatch = b.category === current.category ? 0 : 1;
    return aMatch - bMatch;
  });

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

function closeArticle() {
  const feedView = document.getElementById('news-feed');
  const readerView = document.getElementById('article-viewer');

  readerView.classList.add('hidden');
  feedView.classList.remove('hidden');

  // Scroll back to feed
  const section = document.getElementById('insights');
  if (section) section.scrollIntoView({ behavior: 'smooth' });
}

// =========================================================
// ANIMATED COUNTERS
// =========================================================
function initCounters() {
  const counters = document.querySelectorAll('[data-counter]');

  counters.forEach(counter => {
    const target = parseInt(counter.dataset.counter);
    const duration = 2000;
    const step = target / (duration / 16);
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

    // Start animation when element is visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          updateCounter();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    observer.observe(counter);
  });
}

function formatNumber(num) {
  return num.toLocaleString('en-GB');
}

// =========================================================
// LIVE ATTACK MAP SIMULATION
// =========================================================
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

function startAttackSimulation() {
  // Simulate attacks every 2-4 seconds
  setInterval(() => {
    simulateAttack();
  }, 2000 + Math.random() * 2000);

  // Initial attacks
  for (let i = 0; i < 5; i++) {
    setTimeout(() => simulateAttack(), i * 500);
  }
}

function simulateAttack() {
  const sourceIndex = Math.floor(Math.random() * attackCountries.length);
  const targetIndex = Math.floor(Math.random() * attackCountries.length);

  if (sourceIndex === targetIndex) return;

  const source = attackCountries[sourceIndex];
  const target = attackCountries[targetIndex];
  const attackType = attackTypes[Math.floor(Math.random() * attackTypes.length)];

  // Update stats
  attackStats.total++;
  attackType.count++;

  // 70% chance of being blocked
  if (Math.random() < 0.7) {
    attackStats.blocked++;
  } else {
    attackStats.active++;
    setTimeout(() => attackStats.active--, 5000);
  }

  // Create attack visual
  createAttackLine(source, target, attackType.color);
  updateThreatStats();
}

function createAttackLine(source, target, color) {
  const container = document.querySelector('.attack-lines');
  if (!container) return;

  const line = document.createElement('div');
  line.className = 'attack-animation';
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

  // Remove after animation
  setTimeout(() => line.remove(), 1500);
}

function updateThreatStats() {
  const elements = {
    total: document.querySelector('[data-stat="total"]'),
    blocked: document.querySelector('[data-stat="blocked"]'),
    active: document.querySelector('[data-stat="active"]')
  };

  if (elements.total) elements.total.textContent = formatNumber(attackStats.total);
  if (elements.blocked) elements.blocked.textContent = formatNumber(attackStats.blocked);
  if (elements.active) elements.active.textContent = attackStats.active;

  // Update attack type list
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
// REPORT CRIME FORM
// =========================================================
let currentFormStep = 1;
let selectedCategory = null;

function initReportForm() {
  updateFormProgress();
}

function selectCategory(element, category) {
  // Remove previous selection
  document.querySelectorAll('.category-option').forEach(opt => {
    opt.classList.remove('selected');
  });

  // Add selection to clicked element
  element.classList.add('selected');
  selectedCategory = category;
}

function nextFormStep() {
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

function prevFormStep() {
  if (currentFormStep > 1) {
    currentFormStep--;
    updateFormProgress();
    showFormStep(currentFormStep);
  }
}

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

function showFormStep(step) {
  document.querySelectorAll('.form-section').forEach((section, index) => {
    section.classList.toggle('active', index + 1 === step);
  });
}

function submitReport(event) {
  event.preventDefault();

  // Show success message
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

// Expose functions to global scope for HTML onclick handlers
window.toggleTheme = toggleTheme;
window.switchTab = switchTab;
window.nextSlide = nextSlide;
window.prevSlide = prevSlide;
window.goToSlide = goToSlide;
window.selectCategory = selectCategory;
window.nextFormStep = nextFormStep;
window.prevFormStep = prevFormStep;
window.submitReport = submitReport;
