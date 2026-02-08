/**
 * UK Cybersecurity Website - Main JavaScript
 * Handles navigation, theme toggle, article slider, counters, and more
 */

// =========================================================
// GLOBAL STATE
// =========================================================
const state = {
  currentTab: 'home',
  currentSlide: 0,
  articles: [],
  theme: localStorage.getItem('theme') || 'dark',
  sliderInterval: null
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
// ARTICLE SLIDER
// =========================================================
async function loadArticles() {
  try {
    const response = await fetch('../cyber_chatbot_UK1.json');
    const data = await response.json();
    
    // Process and extract unique articles
    state.articles = processArticles(data);
    renderSlider();
    startSliderAutoplay();
  } catch (error) {
    console.error('Error loading articles:', error);
    renderFallbackSlider();
  }
}

function processArticles(data) {
  // Extract meaningful articles with titles
  const articles = [];
  const seenUrls = new Set();
  
  data.forEach(item => {
    if (item.url && !seenUrls.has(item.url) && item.content) {
      seenUrls.add(item.url);
      
      // Extract title from URL or content
      const urlParts = item.url.split('/').filter(p => p);
      const titleFromUrl = urlParts[urlParts.length - 1] || 'Cyber Security';
      const title = titleFromUrl
        .replace(/-/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
      
      // Get excerpt
      const excerpt = item.content.substring(0, 250).trim() + '...';
      
      // Assign category icon based on content
      let icon = '🔒';
      if (item.url.includes('physical')) icon = '🏢';
      else if (item.url.includes('technical')) icon = '💻';
      else if (item.url.includes('human')) icon = '👥';
      else if (item.url.includes('iot')) icon = '📱';
      else if (item.url.includes('threat')) icon = '⚠️';
      else if (item.url.includes('attack')) icon = '🎯';
      else if (item.url.includes('malware')) icon = '🦠';
      else if (item.url.includes('hacker')) icon = '🕵️';
      else if (item.url.includes('career')) icon = '💼';
      
      articles.push({
        title,
        excerpt,
        url: item.url,
        icon,
        category: getCategoryFromUrl(item.url)
      });
    }
  });
  
  // Return top 8 articles for slider
  return articles.slice(0, 8);
}

function getCategoryFromUrl(url) {
  if (url.includes('physical')) return 'Physical Security';
  if (url.includes('technical')) return 'Technical Security';
  if (url.includes('human')) return 'Human Security';
  if (url.includes('iot')) return 'IoT Security';
  if (url.includes('threat')) return 'Threat Intelligence';
  if (url.includes('career')) return 'Careers';
  return 'Cyber Security';
}

function renderSlider() {
  const track = document.querySelector('.slider-track');
  const dotsContainer = document.querySelector('.slider-dots');
  
  if (!track || !state.articles.length) return;
  
  track.innerHTML = state.articles.map((article, index) => `
    <div class="slide">
      <div class="article-card glass-card">
        <div class="article-content">
          <span class="article-tag">${article.category}</span>
          <h2 class="article-title">${article.title}</h2>
          <p class="article-excerpt">${article.excerpt}</p>
          <a href="${article.url}" target="_blank" class="article-link">
            Read More <span>→</span>
          </a>
        </div>
        <div class="article-visual">
          ${article.icon}
        </div>
      </div>
    </div>
  `).join('');
  
  // Render dots
  if (dotsContainer) {
    dotsContainer.innerHTML = state.articles.map((_, index) => `
      <button class="slider-dot ${index === 0 ? 'active' : ''}" onclick="goToSlide(${index})"></button>
    `).join('');
  }
}

function renderFallbackSlider() {
  const fallbackArticles = [
    { title: 'Areas of Cyber Security', excerpt: 'Cyber security is made up of three main areas - physical, technical and human. Understanding all three is essential for comprehensive protection.', icon: '🔒', category: 'Overview', url: '#' },
    { title: 'Physical Cyber Security', excerpt: 'Physical security has been important long before cyber security and continues to be crucial to the safety of cyber information today.', icon: '🏢', category: 'Physical Security', url: '#' },
    { title: 'Technical Cyber Security', excerpt: 'Technical cyber security involves protecting ourselves digitally through antivirus software, ethical hacking, and vulnerability assessments.', icon: '💻', category: 'Technical Security', url: '#' },
    { title: 'Human Cyber Security', excerpt: 'People play a crucial role in their own cyber security as well as that of others. Awareness-raising is key to the human side of security.', icon: '👥', category: 'Human Security', url: '#' }
  ];
  
  state.articles = fallbackArticles;
  renderSlider();
  startSliderAutoplay();
}

function goToSlide(index) {
  state.currentSlide = index;
  updateSlider();
}

function nextSlide() {
  state.currentSlide = (state.currentSlide + 1) % state.articles.length;
  updateSlider();
}

function prevSlide() {
  state.currentSlide = (state.currentSlide - 1 + state.articles.length) % state.articles.length;
  updateSlider();
}

function updateSlider() {
  const track = document.querySelector('.slider-track');
  const dots = document.querySelectorAll('.slider-dot');
  
  if (track) {
    track.style.transform = `translateX(-${state.currentSlide * 100}%)`;
  }
  
  dots.forEach((dot, index) => {
    dot.classList.toggle('active', index === state.currentSlide);
  });
}

function startSliderAutoplay() {
  if (state.sliderInterval) clearInterval(state.sliderInterval);
  state.sliderInterval = setInterval(nextSlide, 6000);
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
