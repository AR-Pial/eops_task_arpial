<template>
  <div class="container mt-5" style="max-width: 420px">
    <h2>Login</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <form @submit.prevent="onSubmit">
      <div class="mb-3">
        <label class="form-label" for="email">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          class="form-control"
          required
        />
      </div>

      <div class="mb-3">
        <label class="form-label" for="password">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="form-control"
          required
          minlength="8"
        />
      </div>

      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? 'Loading...' : 'Login' }}
      </button>
    </form>

    <p class="mt-3">
      No account?
      <router-link :to="{ name: 'register', query: route.query }">Register</router-link>
    </p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import $axios from '../axios'
import API from '../apiUrls'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')

const form = reactive({
  email: '',
  password: '',
})

function redirectAfterAuth(user) {
  if (user && (user.user_type === 'admin' || user.user_type === 'superadmin')) {
    router.push({ name: 'admin-dashboard' })
    return
  }

  const next = typeof route.query.next === 'string' ? route.query.next : '/'
  router.push(next.startsWith('/') ? next : '/')
}

async function onSubmit() {
  loading.value = true
  error.value = ''

  try {
    const { data } = await $axios.post(API.login, {
      email: form.email,
      password: form.password,
    })

    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    redirectAfterAuth(data.user)
  } catch (err) {
    const detail =
      err.response?.data?.non_field_errors?.[0] ||
      err.response?.data?.detail ||
      Object.values(err.response?.data || {})[0]?.[0] ||
      'Login failed'
    error.value = typeof detail === 'string' ? detail : 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
