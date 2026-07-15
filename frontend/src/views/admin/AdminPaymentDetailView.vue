<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Payment details</h2>

    <router-link class="btn btn-sm btn-secondary mb-3" to="/admin/payments">Back</router-link>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <p v-else-if="loading" class="text-muted">Loading...</p>

    <div v-else-if="payment">
      <p>
        Order No.:
        <router-link
          class="link-primary text-decoration-underline"
          :to="`/admin/orders/${payment.order}`"
        >
          {{ payment.order_number }}
        </router-link>
      </p>
      <p>Amount: {{ formatBDT(payment.amount) }}</p>
      <p>
        Provider:
        <span class="text-uppercase">{{ payment.provider }}</span>
      </p>
      <p>
        Transaction ID:
        <code>{{ payment.transaction_id }}</code>
      </p>
      <p>
        Status:
        <span class="badge" :class="statusClass(payment.status)">{{ payment.status }}</span>
      </p>
      <p>Created: {{ formatDate(payment.created_at) }}</p>
      <p>Updated: {{ formatDate(payment.updated_at) }}</p>
    </div>

    <p v-else class="text-muted">Payment not found.</p>
  </AdminLayout>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import $axios from '../../axios'
import API from '../../apiUrls'
import { formatBDT } from '../../utils/money'

const route = useRoute()
const payment = ref(null)
const loading = ref(true)
const error = ref('')

function statusClass(status) {
  if (status === 'success') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-danger'
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function loadPayment(id) {
  loading.value = true
  error.value = ''
  payment.value = null
  try {
    const { data } = await $axios.get(API.paymentDetail(id))
    payment.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load payment.'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadPayment(route.params.id))
watch(
  () => route.params.id,
  (id) => {
    if (id) loadPayment(id)
  },
)
</script>
