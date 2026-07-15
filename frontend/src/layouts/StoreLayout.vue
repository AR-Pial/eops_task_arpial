<template>
  <div class="store-shell">
    <Navbar />
    <main class="store-main">
      <slot />
    </main>
  </div>
</template>

<script setup>
import Navbar from '../components/Navbar.vue'
</script>

<style scoped>
.store-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.store-main {
  flex: 1;
  padding-top: 1.25rem;
  padding-bottom: 2.5rem;
}
</style>
