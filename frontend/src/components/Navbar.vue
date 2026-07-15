<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#mainNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div id="mainNav" class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/">Home</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" :to="{ path: '/', hash: '#products' }">
              Products
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/checkout">
              Checkout ({{ cartCount }})
            </router-link>
          </li>
          <li v-if="isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/orders">My Orders</router-link>
          </li>
          <li v-if="isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/payments">Payments</router-link>
          </li>
          <li v-if="isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/profile">Profile</router-link>
          </li>
        </ul>

        <ul class="navbar-nav align-items-center">
          <template v-if="isLoggedIn">
            <li v-if="userName" class="nav-item">
              <span class="nav-link text-white mb-0">{{ userName }}</span>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#" @click.prevent="logout">Logout</a>
            </li>
          </template>
          <template v-else>
            <li class="nav-item">
              <router-link class="nav-link" to="/login">Login</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/register">Register</router-link>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCart } from '../cart'

const router = useRouter()
const token = ref(localStorage.getItem('token'))
const cartCount = ref(0)

const isLoggedIn = computed(() => !!token.value)

const storedUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
})

const userName = computed(() => {
  const user = storedUser.value
  if (!user) return ''
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ')
  return name || ''
})

function refreshCart() {
  cartCount.value = getCart().reduce((n, item) => n + item.quantity, 0)
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  token.value = null
  router.push({ name: 'home' })
}

onMounted(() => {
  refreshCart()
  window.addEventListener('cart-updated', refreshCart)
  window.addEventListener('storage', refreshCart)
})

onUnmounted(() => {
  window.removeEventListener('cart-updated', refreshCart)
  window.removeEventListener('storage', refreshCart)
})
</script>
