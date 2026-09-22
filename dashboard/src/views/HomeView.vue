<script setup lang="ts">
import { ref, onMounted } from "vue";
import logo from "@/assets/pairo.png";

const loaded = ref(false);
onMounted(() => {
  requestAnimationFrame(() => {
    loaded.value = true;
  });
});
</script>

<template>
  <div class="landing" :class="{ loaded }">
    <!-- ===== Navbar ===== -->
    <nav class="navbar">
      <div class="nav-container">
        <a href="/" class="nav-logo">
          <img :src="logo" alt="Pairo" class="nav-logo-img" />
          <span class="nav-logo-text">Pairo</span>
        </a>
        <div class="landing-nav-links">
          <a href="#" class="landing-nav-link"
            >Product
            <svg class="chevron" width="10" height="10" viewBox="0 0 10 10">
              <path
                d="M2.5 3.5L5 6l2.5-2.5"
                stroke="currentColor"
                stroke-width="1.5"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg
          ></a>
          <a href="#" class="landing-nav-link"
            >Solutions
            <svg class="chevron" width="10" height="10" viewBox="0 0 10 10">
              <path
                d="M2.5 3.5L5 6l2.5-2.5"
                stroke="currentColor"
                stroke-width="1.5"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg
          ></a>
          <a href="#" class="landing-nav-link">Pricing</a>
          <a href="#" class="landing-nav-link">Docs</a>
          <a href="#" class="landing-nav-link"
            >Company
            <svg class="chevron" width="10" height="10" viewBox="0 0 10 10">
              <path
                d="M2.5 3.5L5 6l2.5-2.5"
                stroke="currentColor"
                stroke-width="1.5"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg
          ></a>
        </div>
        <button class="nav-mobile-toggle" aria-label="Menu">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </div>
    </nav>

    <!-- ===== Hero ===== -->
    <section class="hero">
      <!-- Background layers -->
      <div class="bg-grid"></div>
      <div class="bg-glow"></div>

      <!-- Hero text content -->
      <div class="hero-text">
        <a
          href="https://github.com/paschyz/pairo"
          target="_blank"
          rel="noopener"
          class="trust-badge"
        >
          <span class="trust-dot"></span>
          LIVE ON GITHUB
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </a>
        <h1 class="hero-title">
          AI code reviews<br />
          <span class="gradient-text">that actually help</span>
        </h1>
        <p class="hero-subtitle">Ship cleaner code, faster.</p>
        <div class="cta-row">
          <div class="btn-primary-wrap">
            <a
              href="https://github.com/paschyz/pairo"
              target="_blank"
              rel="noopener"
              class="btn-primary"
            >
              Try it for free
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </a>
          </div>
          <a href="#" class="btn-secondary">
            <svg
              class="play-icon"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <polygon points="5,3 19,12 5,21" />
            </svg>
            Demo
          </a>
        </div>
      </div>

      <!-- Mascot -->
      <div class="mascot-wrap">
        <div class="mascot-glow"></div>
        <div class="orbit"></div>
        <img :src="logo" alt="Pairo mascot" class="mascot-img" />
      </div>

      <!-- Handwritten text -->
      <div class="handwritten">
        <span>Better</span><br />
        <span>code together</span>
        <svg
          class="hw-arrow"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="5" y1="19" x2="19" y2="5" />
          <polyline points="9 5 19 5 19 15" />
        </svg>
      </div>

      <!-- Decorative code brackets -->
      <div class="deco-code deco-left">
        <span>&lt;/&gt;</span>
      </div>
      <div class="deco-code deco-right">
        <span>&lt;/&gt;</span>
      </div>

      <!-- ===== Floating Cards ===== -->

      <!-- PR Review Card -->
      <div class="float-card card-pr">
        <div class="fc-header">
          <svg width="20" height="20" viewBox="0 0 16 16" fill="#8b949e">
            <path
              d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"
            />
          </svg>
          <span class="fc-title">Pull Request Review</span>
          <span class="badge-open">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path
                d="M5 2v6M2 5h6"
                stroke="#38D996"
                stroke-width="1.5"
                stroke-linecap="round"
              />
            </svg>
            Open
          </span>
        </div>
        <div class="pr-body">
          <p class="pr-title">feat: add user subscription flow</p>
          <div class="pr-meta">
            <div class="pr-avatar"></div>
            <span class="pr-number">#4821</span>
          </div>
          <div class="pr-author">by taylor-dev &nbsp; 2 hours ago</div>
        </div>
        <div class="pr-divider"></div>
        <div class="pr-review">
          <div class="pr-review-header">
            <img :src="logo" class="pr-pairo-icon" />
            <div>
              <strong>Pairo</strong> reviewed 5 minutes ago
              <div class="pr-review-counts">3 issues · 2 suggestions</div>
            </div>
          </div>
          <div class="pr-findings">
            <div class="pr-finding">
              <span class="dot dot-danger"></span> 1 potential bug
            </div>
            <div class="pr-finding">
              <span class="dot dot-warning"></span> 1 security suggestion
            </div>
            <div class="pr-finding">
              <span class="dot dot-info"></span> 2 code improvements
            </div>
          </div>
          <a class="pr-view-link"
            >View full review
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" /></svg
          ></a>
        </div>
      </div>

      <!-- AI Suggestion Card -->
      <div class="float-card card-suggestion">
        <div class="fc-header">
          <span class="sparkle">✦</span>
          <span class="fc-title">AI Suggestion</span>
        </div>
        <div class="suggestion-tabs">
          <div class="stab stab-before">Before</div>
          <div class="stab stab-after">After</div>
        </div>
        <div class="suggestion-code">
          <div class="code-before">
            <div class="code-line">
              <span class="ln">1</span> <span class="kw">if</span> (user) {
            </div>
            <div class="code-line">
              <span class="ln">2</span> <span class="kw">return</span> user.name
            </div>
            <div class="code-line"><span class="ln">3</span> }</div>
            <div class="code-line">
              <span class="ln">4</span> <span class="kw">return</span>
              <span class="val">null</span>
            </div>
          </div>
          <div class="code-after">
            <div class="code-line">
              <span class="ln">1</span>
              <span class="kw">return</span> user?.name
            </div>
            <div class="code-line">
              <span class="ln">2</span> ?? <span class="val">null</span>
            </div>
            <div class="code-line"><span class="ln">3</span></div>
          </div>
        </div>
        <div class="suggestion-footer">
          <span>Apply suggestion</span>
          <div class="kbd-group">
            <kbd>⌘</kbd>
            <kbd>↵</kbd>
          </div>
        </div>
      </div>

      <!-- Security Alert Card -->
      <div class="float-card card-security">
        <span class="badge-high">High</span>
        <div class="fc-header">
          <span class="dot-lg dot-danger"></span>
          <span class="fc-title">Security Alert</span>
        </div>
        <p class="sec-title">Potential SQL injection risk</p>
        <p class="sec-desc">
          User input is concatenated into a query without sanitization.
        </p>
        <div class="sec-code">
          <div class="code-line">
            <span class="ln">12</span> <span class="kw">const</span> query =
            <span class="str">`SELECT * FROM users</span>
          </div>
          <div class="code-line">
            <span class="ln">13</span>
            <span class="str"
              >WHERE id = <span class="interp">${userId}</span>`</span
            >
          </div>
        </div>
        <a class="sec-fix-link"
          >View fix
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" /></svg
        ></a>
      </div>

      <!-- Impact Card -->
      <div class="float-card card-impact">
        <div class="fc-header">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#A6ABB5"
            stroke-width="2"
            stroke-linecap="round"
          >
            <rect x="3" y="12" width="4" height="9" />
            <rect x="10" y="8" width="4" height="13" />
            <rect x="17" y="3" width="4" height="18" />
          </svg>
          <span class="fc-title">Impact</span>
          <span class="impact-period"
            >Last 30 days
            <svg width="10" height="10" viewBox="0 0 10 10">
              <path
                d="M2.5 3.5L5 6l2.5-2.5"
                stroke="currentColor"
                stroke-width="1.5"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg
          ></span>
        </div>
        <div class="impact-stats">
          <div class="impact-stat">
            <span class="impact-num">127</span>
            <span class="impact-label">PRs reviewed</span>
          </div>
          <div class="impact-stat">
            <span class="impact-num">48</span>
            <span class="impact-label">Bugs caught</span>
          </div>
          <div class="impact-stat">
            <span class="impact-num">12</span>
            <span class="impact-label">Security issues</span>
          </div>
          <div class="impact-stat">
            <span class="impact-num">3.2h</span>
            <span class="impact-label">Dev time saved</span>
          </div>
        </div>
        <div class="impact-chart">
          <div class="bar" style="height: 40%"></div>
          <div class="bar" style="height: 65%"></div>
          <div class="bar" style="height: 45%"></div>
          <div class="bar" style="height: 80%"></div>
          <div class="bar" style="height: 55%"></div>
          <div class="bar" style="height: 90%"></div>
          <div class="bar" style="height: 70%"></div>
          <div class="bar" style="height: 60%"></div>
          <div class="bar" style="height: 95%"></div>
          <div class="bar" style="height: 75%"></div>
        </div>
        <div class="impact-metric">
          <span class="metric-up">↑ 40%</span>
          <span class="metric-label">Fewer production issues</span>
        </div>
      </div>

      <!-- Horizon -->
      <div class="horizon"></div>
    </section>
  </div>
</template>

<style scoped>
/* ========== Base ========== */
.landing {
  --bg: #08090d;
  --bg-card: rgba(15, 17, 24, 0.9);
  --border: rgba(255, 255, 255, 0.08);
  --text: #f5f7fa;
  --text-secondary: #a6abb5;
  --text-muted: #6c7280;
  --orange: #ff7a32;
  --orange-light: #ff9a59;
  --orange-glow: rgba(255, 122, 50, 0.25);
  --success: #38d996;
  --danger: #ff5d61;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family:
    "Space Grotesk",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Roboto,
    sans-serif;
  overflow-x: hidden;
}

/* ========== Navbar ========== */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 84px;
  background: rgba(8, 9, 13, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.nav-container {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 40px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text);
  flex-shrink: 0;
}

.nav-logo-img {
  width: 30px;
  height: 30px;
  border-radius: 8px;
}

.nav-logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.landing-nav-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
}

.landing-nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  transition: color 0.15s;
}

.landing-nav-link:hover {
  color: var(--text);
}

.chevron {
  opacity: 0.6;
}

.nav-mobile-toggle {
  display: none;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
}

/* ========== Hero Section ========== */
.hero {
  position: relative;
  min-height: 760px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

/* Background grid */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 64px 64px;
  pointer-events: none;
  z-index: 0;
}

/* Orange glow */
.bg-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at 50% 55%,
    rgba(255, 122, 50, 0.13),
    transparent 35%
  );
  pointer-events: none;
  z-index: 0;
}

/* ========== Hero Text ========== */
.hero-text {
  position: relative;
  z-index: 10;
  text-align: center;
  padding-top: 48px;
  max-width: 760px;
  margin: 0 auto;
  padding-left: 20px;
  padding-right: 20px;
}

.trust-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  padding: 8px 18px;
  border-radius: 100px;
  margin-bottom: 28px;
  text-decoration: none;
  transition:
    border-color 0.15s,
    color 0.15s;
}

.trust-badge:hover {
  color: var(--text);
  border-color: rgba(255, 255, 255, 0.16);
}

.trust-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
  position: relative;
}

.trust-dot::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: #22c55e;
  animation: dotExpand 1.5s ease-out infinite;
}

@keyframes dotExpand {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(3);
    opacity: 0;
  }
}

.hero-title {
  font-size: 72px;
  font-weight: 700;
  line-height: 0.98;
  letter-spacing: -0.04em;
  color: var(--text);
  margin: 0;
}

.gradient-text {
  background: linear-gradient(90deg, #e05500, #ffcc66, #e05500, #ffcc66, #e05500);
  background-size: 200% 100%;
  animation: gradient-cycle 3s ease infinite;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

@keyframes gradient-cycle {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

.hero-subtitle {
  margin-top: 24px;
  font-size: 18px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.desktop-br {
  display: block;
}

.cta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 36px;
}

.btn-primary-wrap {
  position: relative;
  border-radius: 12px;
  padding: 2px;
  overflow: hidden;
}

.btn-primary-wrap::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 300%;
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  background: conic-gradient(
    from 0deg,
    transparent 0%,
    transparent 44%,
    rgba(255, 220, 170, 0.7) 48%,
    #fff 50%,
    rgba(255, 220, 170, 0.7) 52%,
    transparent 56%,
    transparent 100%
  );
  animation: borderSpin 2.5s linear infinite;
}

@keyframes borderSpin {
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

.btn-primary {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 52px;
  padding: 0 34px;
  background: linear-gradient(135deg, #ff984f 0%, #ff6b1a 50%, #ff8534 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  border-radius: 10.5px;
  text-decoration: none;
  border: none;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.3),
    0 8px 24px var(--orange-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.btn-primary::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.15) 0%,
    transparent 50%
  );
  border-radius: inherit;
  pointer-events: none;
}

.btn-primary::after {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.1) 0%,
    transparent 60%
  );
  opacity: 0;
  transform: scale(0.5);
  transition:
    opacity 0.3s,
    transform 0.3s;
  pointer-events: none;
}

.btn-primary:hover::after {
  opacity: 1;
  transform: scale(1);
}

.btn-primary:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow:
    0 0 0 1px rgba(255, 117, 40, 0.4),
    0 2px 4px rgba(0, 0, 0, 0.3),
    0 16px 48px rgba(255, 122, 50, 0.45),
    0 4px 12px rgba(255, 122, 50, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  filter: brightness(1.1);
}

.btn-primary:active {
  transform: translateY(0) scale(0.98);
  filter: brightness(0.95);
  transition-duration: 0.1s;
}

.btn-secondary {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  height: 52px;
  padding: 0 34px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text);
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.01em;
  border-radius: 10px;
  text-decoration: none;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.3),
    0 4px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.btn-secondary::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
  border-radius: inherit;
  pointer-events: none;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.22);
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.3),
    0 12px 32px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transform: translateY(-3px) scale(1.02);
  filter: brightness(1.1);
}

.btn-secondary:active {
  transform: translateY(0) scale(0.98);
  filter: brightness(0.95);
  transition-duration: 0.1s;
}

.play-icon {
  opacity: 0.8;
}

/* ========== Mascot ========== */
.mascot-wrap {
  position: absolute;
  top: 370px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  width: 380px;
  height: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mascot-glow {
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 122, 50, 0.2), transparent 70%);
  pointer-events: none;
}

.orbit {
  position: absolute;
  width: 420px;
  height: 160px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 50%;
  transform: rotateX(70deg);
  pointer-events: none;
}

.mascot-img {
  position: relative;
  width: 200px;
  height: 200px;
  border-radius: 24px;
  animation: mascotFloat 4.5s ease-in-out infinite;
  filter: drop-shadow(0 20px 60px rgba(255, 122, 50, 0.3));
}

@keyframes mascotFloat {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(1.5deg);
  }
}

/* ========== Handwritten text ========== */
.handwritten {
  position: absolute;
  top: 390px;
  right: 30%;
  z-index: 6;
  font-style: italic;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.3;
  transform: rotate(-3deg);
  pointer-events: none;
}

.hw-arrow {
  margin-left: 4px;
  vertical-align: middle;
  opacity: 0.35;
}

/* ========== Decorative Code Brackets ========== */
.deco-code {
  position: absolute;
  z-index: 3;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  background: rgba(15, 17, 24, 0.6);
  color: rgba(255, 255, 255, 0.15);
  font-size: 16px;
  font-weight: 600;
  pointer-events: none;
}

.deco-left {
  left: 3%;
  top: 320px;
  animation: decoFloat 6s ease-in-out infinite;
}

.deco-right {
  right: 4%;
  top: 560px;
  animation: decoFloat 6s ease-in-out infinite 3s;
}

@keyframes decoFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

/* ========== Floating Cards (shared) ========== */
.float-card {
  position: absolute;
  z-index: 4;
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(16px);
  padding: 20px;
  opacity: 0;
  transform: translateY(40px) scale(0.9);
  filter: blur(4px);
  transition:
    transform 0.4s ease,
    box-shadow 0.4s ease,
    filter 0.4s ease,
    opacity 0.4s ease;
}

.loaded .float-card {
  animation: cardEnter 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.float-card:hover {
  opacity: 1 !important;
  transform: translateY(-4px) rotate(0deg) scale(1) !important;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
  filter: blur(0) !important;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.9);
    filter: blur(4px);
  }
  60% {
    filter: blur(0);
  }
  to {
    opacity: 0.55;
    transform: translateY(0) scale(0.92);
    filter: blur(0);
  }
}

/* Card header shared */
.fc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.fc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

/* ========== PR Review Card ========== */
.card-pr {
  left: 8%;
  top: 180px;
  width: 330px;
  transform: rotate(-4deg);
  animation-delay: 0.4s;
}

.loaded .card-pr {
  animation:
    cardEnterPR 1s cubic-bezier(0.16, 1, 0.3, 1) 0.4s forwards,
    cardFloatA 6s ease-in-out 1.5s infinite;
}

@keyframes cardEnterPR {
  from { opacity: 0; transform: translateY(40px) scale(0.9) rotate(-4deg); filter: blur(4px); }
  60% { filter: blur(0); }
  to { opacity: 0.55; transform: translateY(0) scale(0.92) rotate(-4deg); filter: blur(0); }
}

@keyframes cardFloatA {
  0%,
  100% {
    transform: translateY(0) rotate(-4deg);
  }
  50% {
    transform: translateY(-6px) rotate(-3.5deg);
  }
}

.badge-open {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--success);
  background: rgba(56, 217, 150, 0.1);
  padding: 3px 10px;
  border-radius: 8px;
}

.pr-body {
  margin-bottom: 12px;
}

.pr-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}

.pr-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.pr-avatar {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4a9eff, #7c6ef0);
}

.pr-number {
  font-size: 12px;
  color: var(--text-muted);
}

.pr-author {
  font-size: 12px;
  color: var(--text-muted);
}

.pr-divider {
  height: 1px;
  background: var(--border);
  margin: 12px 0;
}

.pr-review-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.pr-pairo-icon {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  flex-shrink: 0;
  margin-top: 1px;
}

.pr-review-header strong {
  font-size: 13px;
  font-weight: 600;
}

.pr-review-header div {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}

.pr-review-counts {
  color: var(--orange);
  font-weight: 600;
  font-size: 12px;
  margin-top: 2px;
}

.pr-findings {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.pr-finding {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-lg {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-danger {
  background: var(--danger);
}
.dot-warning {
  background: #ffb347;
}
.dot-info {
  background: #5b9df0;
}

.pr-view-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.pr-view-link:hover {
  color: var(--text);
}

/* ========== AI Suggestion Card ========== */
.card-suggestion {
  left: 6%;
  top: 520px;
  width: 390px;
  transform: rotate(-1deg);
  animation-delay: 0.7s;
}

.loaded .card-suggestion {
  animation:
    cardEnterSuggestion 1s cubic-bezier(0.16, 1, 0.3, 1) 0.7s forwards,
    cardFloatB 7s ease-in-out 1.8s infinite;
}

@keyframes cardEnterSuggestion {
  from { opacity: 0; transform: translateY(40px) scale(0.9) rotate(-1deg); filter: blur(4px); }
  60% { filter: blur(0); }
  to { opacity: 0.55; transform: translateY(0) scale(0.92) rotate(-1deg); filter: blur(0); }
}

@keyframes cardFloatB {
  0%,
  100% {
    transform: translateY(0) rotate(-1deg);
  }
  50% {
    transform: translateY(-8px) rotate(-0.5deg);
  }
}

.sparkle {
  color: var(--orange-light);
  font-size: 16px;
}

.suggestion-tabs {
  display: flex;
  margin-bottom: 0;
  border-radius: 0;
  overflow: hidden;
}

.stab {
  flex: 1;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.stab-before {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
}

.stab-after {
  background: rgba(56, 217, 150, 0.08);
  color: var(--success);
}

.suggestion-code {
  display: flex;
  font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.7;
}

.code-before,
.code-after {
  flex: 1;
  padding: 12px;
}

.code-before {
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid var(--border);
}

.code-after {
  background: rgba(56, 217, 150, 0.03);
}

.code-line {
  white-space: pre;
  color: var(--text-secondary);
}

.ln {
  color: var(--text-muted);
  opacity: 0.5;
  margin-right: 8px;
  user-select: none;
}

.kw {
  color: #c678dd;
}
.val {
  color: #d19a66;
}
.str {
  color: #98c379;
}
.interp {
  color: var(--orange-light);
}

.suggestion-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 0;
  font-size: 12px;
  color: var(--text-muted);
}

.kbd-group {
  display: flex;
  gap: 4px;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  font-family: inherit;
  font-size: 11px;
  color: var(--text-muted);
}

/* ========== Security Alert Card ========== */
.card-security {
  right: 6%;
  top: 180px;
  width: 350px;
  transform: rotate(4deg);
  animation-delay: 0.55s;
}

.loaded .card-security {
  animation:
    cardEnterSecurity 1s cubic-bezier(0.16, 1, 0.3, 1) 0.55s forwards,
    cardFloatC 5.5s ease-in-out 1.6s infinite;
}

@keyframes cardEnterSecurity {
  from { opacity: 0; transform: translateY(40px) scale(0.9) rotate(4deg); filter: blur(4px); }
  60% { filter: blur(0); }
  to { opacity: 0.55; transform: translateY(0) scale(0.92) rotate(4deg); filter: blur(0); }
}

@keyframes cardFloatC {
  0%,
  100% {
    transform: translateY(0) rotate(4deg);
  }
  50% {
    transform: translateY(-7px) rotate(3.5deg);
  }
}

.badge-high {
  position: absolute;
  top: 14px;
  right: 14px;
  font-size: 11px;
  font-weight: 700;
  color: var(--danger);
  background: rgba(255, 93, 97, 0.12);
  padding: 3px 10px;
  border-radius: 8px;
}

.sec-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.sec-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 14px;
}

.sec-code {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 12px;
  font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.7;
  margin-bottom: 14px;
}

.sec-fix-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.sec-fix-link:hover {
  color: var(--text);
}

/* ========== Impact Card ========== */
.card-impact {
  right: 9%;
  top: 500px;
  width: 360px;
  animation-delay: 0.85s;
}

.loaded .card-impact {
  animation:
    cardEnter 1s cubic-bezier(0.16, 1, 0.3, 1) 0.85s forwards,
    cardFloatD 6.5s ease-in-out 1.9s infinite;
}

@keyframes cardFloatD {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.impact-period {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.impact-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.impact-stat {
  text-align: center;
}

.impact-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.impact-label {
  font-size: 10px;
  color: var(--text-muted);
  line-height: 1.3;
}

.impact-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 48px;
  margin-bottom: 14px;
  padding: 0 4px;
}

.bar {
  flex: 1;
  background: linear-gradient(180deg, var(--orange), rgba(255, 122, 50, 0.4));
  border-radius: 3px 3px 0 0;
  min-height: 4px;
}

.impact-metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-up {
  font-size: 18px;
  font-weight: 700;
  color: var(--orange);
}

.metric-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* ========== Horizon ========== */
.horizon {
  position: absolute;
  bottom: -140px;
  left: -10%;
  right: -10%;
  height: 240px;
  background: #060810;
  border-radius: 50% 50% 0 0 / 100% 100% 0 0;
  box-shadow:
    0 -1px 0 rgba(100, 140, 255, 0.06),
    0 -4px 30px rgba(100, 140, 255, 0.03);
  z-index: 2;
}

/* ========== Responsive ========== */

/* Laptop */
@media (max-width: 1400px) {
  .hero-title {
    font-size: 64px;
  }
  .card-pr {
    left: 4%;
    width: 300px;
  }
  .card-suggestion {
    left: 2%;
    width: 350px;
  }
  .card-security {
    right: 3%;
    width: 320px;
  }
  .card-impact {
    right: 4%;
    width: 330px;
  }
}

/* Tablet */
@media (max-width: 1100px) {
  .landing-nav-links {
    display: none;
  }
  .nav-mobile-toggle {
    display: flex;
  }
  .hero-title {
    font-size: 56px;
  }
  .float-card {
    transform: rotate(0deg) !important;
  }
  .card-pr {
    left: 2%;
    width: 280px;
    top: 200px;
  }
  .card-suggestion {
    left: 1%;
    width: 300px;
    top: 500px;
  }
  .card-security {
    right: 1%;
    width: 280px;
    top: 200px;
  }
  .card-impact {
    right: 2%;
    width: 300px;
    top: 480px;
  }
  .handwritten {
    display: none;
  }
  .deco-code {
    display: none;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .navbar {
    height: 64px;
  }

  .landing-nav-links {
    display: none;
  }

  .nav-mobile-toggle {
    display: flex;
  }

  .hero {
    min-height: auto;
    padding-bottom: 40px;
  }

  .hero-text {
    padding-top: 32px;
  }

  .hero-title {
    font-size: 44px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .desktop-br {
    display: none;
  }

  .cta-row {
    flex-direction: column;
    gap: 12px;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }

  .mascot-wrap {
    position: relative;
    top: auto;
    left: auto;
    transform: none;
    width: 280px;
    height: 280px;
    margin: 32px auto 0;
  }

  .mascot-img {
    width: 140px;
    height: 140px;
  }

  .mascot-glow {
    width: 200px;
    height: 200px;
  }

  .orbit {
    display: none;
  }

  /* Cards become stacked below mascot */
  .float-card {
    position: relative;
    top: auto !important;
    left: auto !important;
    right: auto !important;
    width: 100% !important;
    max-width: 400px;
    margin: 16px auto 0;
    transform: none !important;
  }

  .card-suggestion {
    display: none;
  }

  .handwritten {
    display: none;
  }
  .deco-code {
    display: none;
  }
  .horizon {
    display: none;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 36px;
  }
  .trust-logo svg {
    display: none;
  }
}
</style>
