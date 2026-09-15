<script setup lang="ts">
</script>

<template>
  <div class="app">
    <nav class="sidebar">
      <div class="logo">
        <span class="logo-icon">◈</span>
        <span class="logo-text">pairo</span>
      </div>
      <ul class="nav-links">
        <li><RouterLink to="/" class="nav-link active">Dashboard</RouterLink></li>
        <li><a class="nav-link disabled">Repositories</a></li>
        <li><a class="nav-link disabled">Reviews</a></li>
        <li><a class="nav-link disabled">Settings</a></li>
      </ul>
    </nav>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f1117;
  color: #e1e4e8;
  min-height: 100vh;
}

.app {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: #161821;
  border-right: 1px solid #2a2d3a;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 0.75rem 1.5rem;
  border-bottom: 1px solid #2a2d3a;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 1.4rem;
  color: #7c6ef0;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.nav-links {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-link {
  display: block;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  color: #8b8fa3;
  text-decoration: none;
  font-size: 0.9rem;
  transition: background 0.15s, color 0.15s;
}

.nav-link:hover {
  background: #1e2030;
  color: #e1e4e8;
}

.nav-link.active,
.nav-link.router-link-active {
  background: #1e2030;
  color: #e1e4e8;
  font-weight: 500;
}

.nav-link.disabled {
  opacity: 0.4;
  pointer-events: none;
}

.content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}
</style>
