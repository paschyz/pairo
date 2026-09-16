<script setup lang="ts">
</script>

<template>
  <div class="home">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/" class="brand">pairo</RouterLink>
        <RouterLink to="/dashboard" class="link-dash">Dashboard</RouterLink>
      </div>
    </header>

    <section class="hero">
      <p class="label">Automated code review</p>
      <h1>Catch bugs before<br />your team does</h1>
      <p class="sub">
        Pairo reads every pull request with full repo context
        and posts review comments in seconds.
      </p>
      <RouterLink to="/dashboard" class="cta">Open Dashboard</RouterLink>
    </section>

    <section class="grid">
      <div class="card">
        <h3>Fast</h3>
        <p>Reviews land before your first reviewer opens the PR.</p>
      </div>
      <div class="card">
        <h3>Contextual</h3>
        <p>Understands your patterns, conventions, and history.</p>
      </div>
      <div class="card">
        <h3>Native</h3>
        <p>Inline GitHub comments. Nothing to install or switch to.</p>
      </div>
    </section>

    <footer class="foot">pairo</footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  border-bottom: 1px solid #1e2030;
}

.topbar-inner {
  max-width: 720px;
  margin: 0 auto;
  padding: 1.25rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  text-decoration: none;
  color: #e1e4e8;
}

.link-dash {
  color: #555a6e;
  text-decoration: none;
  font-size: 0.85rem;
}

.link-dash:hover {
  color: #e1e4e8;
}

.hero {
  max-width: 720px;
  margin: 0 auto;
  padding: 8rem 2rem 5rem;
}

.label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #555a6e;
  margin-bottom: 1rem;
}

h1 {
  font-size: 2.75rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.sub {
  margin-top: 1rem;
  font-size: 1.05rem;
  color: #7a7f94;
  line-height: 1.6;
  max-width: 440px;
}

.cta {
  display: inline-block;
  margin-top: 2rem;
  padding: 0.6rem 1.5rem;
  background: #F28C38;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.cta:hover {
  background: #D97A2E;
}

.grid {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 2rem 4rem;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.card {
  border: 1px solid #1e2030;
  border-radius: 8px;
  padding: 1.5rem;
}

.card h3 {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.card p {
  font-size: 0.85rem;
  color: #7a7f94;
  line-height: 1.5;
}

.foot {
  margin-top: auto;
  border-top: 1px solid #1e2030;
  padding: 1.5rem 2rem;
  text-align: center;
  color: #3a3d4a;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
