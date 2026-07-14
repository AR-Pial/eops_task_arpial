<template>
  <div class="admin-shell d-flex">
    <aside class="admin-sidebar bg-dark text-white p-3">
      <ul class="nav nav-pills flex-column gap-1">
        <li class="nav-item">
          <router-link class="nav-link text-white" :class="{ active: isActive('admin-dashboard') }" to="/admin">
            Dashboard
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link text-white" :class="{ active: isActive('admin-products') }" to="/admin/products">
            Products
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link text-white" :class="{ active: isActive('admin-categories') }" to="/admin/categories">
            Categories
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link text-white" :class="{ active: isActive('admin-orders') }" to="/admin/orders">
            Orders
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link text-white" :class="{ active: isActive('admin-payments') }" to="/admin/payments">
            Payments
          </router-link>
        </li>
      </ul>
    </aside>

    <div class="admin-main flex-grow-1">
      <header class="admin-header border-bottom bg-white px-4 py-3 d-flex justify-content-between align-items-center">
        <router-link class="nav-link px-0 text-secondary" to="/">Back to store</router-link>
        <div class="d-flex align-items-center gap-3">
          <span v-if="displayName" class="text-muted">{{ displayName }}</span>
          <router-link class="nav-link px-0" to="/profile">Profile</router-link>
          <a class="nav-link px-0" href="#" @click.prevent="logout">Logout</a>
        </div>
      </header>

      <main class="p-4">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const displayName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    if (!user) return ''
    const name = [user.first_name, user.last_name].filter(Boolean).join(' ')
    return name || user.email || ''
  } catch {
    return ''
  }
})

function isActive(name) {
  return route.name === name
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push({ name: 'login' })
}
</script>

<style scoped>
.admin-shell {
  min-height: 100vh;
}

.admin-sidebar {
  width: 240px;
  min-height: 100vh;
}

.admin-sidebar .nav-link.active {
  background-color: rgba(255, 255, 255, 0.15);
}

.admin-sidebar .nav-link:hover {
  background-color: rgba(255, 255, 255, 0.08);
}

.admin-main {
  background: #f5f6f8;
}

.admin-main :deep(table.dataTable thead th),
.admin-main :deep(table.dataTable tbody td) {
  text-align: left !important;
}
</style>
