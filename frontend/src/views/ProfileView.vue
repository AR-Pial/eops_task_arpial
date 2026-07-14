<template>
  <div>
    <Navbar />

    <div class="container" style="max-width: 520px">
      <h2>Profile</h2>

      <div v-if="loadError" class="alert alert-danger">{{ loadError }}</div>
      <div v-if="success" class="alert alert-success">Profile updated.</div>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <form v-if="!loadError" @submit.prevent="onSubmit">
        <div class="mb-3">
          <label class="form-label" for="email">Email</label>
          <input id="email" v-model="form.email" type="email" class="form-control" disabled />
        </div>

        <div class="mb-3">
          <label class="form-label" for="user_type">User type</label>
          <input id="user_type" v-model="form.user_type" type="text" class="form-control" disabled />
        </div>

        <div class="mb-3">
          <label class="form-label" for="first_name">First name</label>
          <input id="first_name" v-model="form.first_name" type="text" class="form-control" />
        </div>

        <div class="mb-3">
          <label class="form-label" for="last_name">Last name</label>
          <input id="last_name" v-model="form.last_name" type="text" class="form-control" />
        </div>

        <div class="mb-3">
          <label class="form-label" for="phone">Phone number</label>
          <input id="phone" v-model="form.phone" type="tel" class="form-control" />
        </div>

        <div class="mb-3">
          <label class="form-label" for="address">Address</label>
          <textarea id="address" v-model="form.address" class="form-control" rows="3"></textarea>
        </div>

        <button class="btn btn-primary" type="submit" :disabled="loading || fetching">
          {{ loading ? 'Saving...' : 'Save changes' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import $axios from '../axios'
import API from '../apiUrls'

const fetching = ref(true)
const loading = ref(false)
const error = ref('')
const loadError = ref('')
const success = ref(false)

const form = reactive({
  email: '',
  user_type: '',
  first_name: '',
  last_name: '',
  phone: '',
  address: '',
})

function applyUser(user) {
  form.email = user.email || ''
  form.user_type = user.user_type || 'customer'
  form.first_name = user.first_name || ''
  form.last_name = user.last_name || ''
  form.phone = user.phone || ''
  form.address = user.address || ''
}

async function loadProfile() {
  fetching.value = true
  loadError.value = ''

  try {
    const { data } = await $axios.get(API.me)
    applyUser(data)
    localStorage.setItem('user', JSON.stringify(data))
  } catch {
    const cached = localStorage.getItem('user')
    if (cached) {
      applyUser(JSON.parse(cached))
    } else {
      loadError.value = 'Could not load profile.'
    }
  } finally {
    fetching.value = false
  }
}

async function onSubmit() {
  loading.value = true
  error.value = ''
  success.value = false

  try {
    const { data } = await $axios.patch(API.me, {
      first_name: form.first_name,
      last_name: form.last_name,
      phone: form.phone,
      address: form.address,
    })
    applyUser(data)
    localStorage.setItem('user', JSON.stringify(data))
    success.value = true
  } catch (err) {
    const payload = err.response?.data
    const first =
      payload?.phone?.[0] ||
      payload?.address?.[0] ||
      payload?.detail ||
      Object.values(payload || {})[0]?.[0] ||
      'Update failed'
    error.value = typeof first === 'string' ? first : 'Update failed'
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)
</script>
