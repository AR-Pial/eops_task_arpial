<template>
  <div class="container mt-5" style="max-width: 420px">
    <h2>Register</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <form @submit.prevent="onSubmit">
      <div class="mb-3">
        <label class="form-label" for="first_name">First name</label>
        <input id="first_name" v-model="form.first_name" type="text" class="form-control" />
      </div>

      <div class="mb-3">
        <label class="form-label" for="last_name">Last name</label>
        <input id="last_name" v-model="form.last_name" type="text" class="form-control" />
      </div>

      <div class="mb-3">
        <label class="form-label" for="email">Email</label>
        <input id="email" v-model="form.email" type="email" class="form-control" required />
      </div>

      <div class="mb-3">
        <label class="form-label" for="phone">Phone number</label>
        <input id="phone" v-model="form.phone" type="tel" class="form-control" />
      </div>

      <div class="mb-3">
        <label class="form-label" for="address">Address</label>
        <textarea id="address" v-model="form.address" class="form-control" rows="2"></textarea>
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
        {{ loading ? 'Loading...' : 'Register' }}
      </button>
    </form>

    <p class="mt-3">
      Already have an account?
      <router-link :to="{ name: 'login', query: route.query }">Login</router-link>
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
  first_name: '',
  last_name: '',
  phone: '',
  address: '',
})

function redirectAfterAuth() {
  const next = typeof route.query.next === 'string' ? route.query.next : '/'
  router.push(next.startsWith('/') ? next : '/')
}

async function onSubmit() {
  loading.value = true
  error.value = ''

  try {
    const { data } = await $axios.post(API.register, { ...form })

    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    redirectAfterAuth()
  } catch (err) {
    const payload = err.response?.data
    const first =
      payload?.email?.[0] ||
      payload?.password?.[0] ||
      payload?.detail ||
      Object.values(payload || {})[0]?.[0] ||
      'Registration failed'
    error.value = typeof first === 'string' ? first : 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
