<template>
  <AdminLayout>
    <h2 class="h4 mb-3">
      Order No. {{ order?.number || '—' }}
    </h2>

    <router-link class="btn btn-sm btn-secondary mb-3" to="/admin/orders">Back</router-link>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <p v-else-if="loading" class="text-muted">Loading...</p>

    <div v-else-if="order">
      <p>
        Status:
        <span class="badge" :class="statusClass(order.status)">{{ order.status }}</span>
      </p>
      <div class="d-flex flex-column flex-lg-row flex-wrap column-gap-4 row-gap-1 mb-3">
        <div v-if="customerName(order)">
          <span class="text-muted">Name:</span>
          {{ customerName(order) }}
        </div>
        <div>
          <span class="text-muted">Email:</span>
          {{ order.user_email || '—' }}
        </div>
      </div>
      <p>Date: {{ formatDate(order.created_at) }}</p>

      <h5 class="h6 mt-4">Items</h5>
      <table class="table table-bordered">
        <thead>
          <tr>
            <th>Serial</th>
            <th>Product</th>
            <th>Qty</th>
            <th>Price</th>
            <th>Subtotal</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in order.items" :key="index">
            <td>{{ index + 1 }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.quantity }}</td>
            <td>{{ formatBDT(item.price) }}</td>
            <td>{{ formatBDT(item.subtotal) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th colspan="4" class="text-end">Total</th>
            <th>{{ formatBDT(order.total_amount) }}</th>
          </tr>
        </tfoot>
      </table>

      <h5 class="h6 mt-4">Payments</h5>
      <p v-if="!order.payments?.length" class="text-muted small">No payments for this order.</p>
      <table v-else class="table table-bordered">
        <thead>
          <tr>
            <th>Serial</th>
            <th>Provider</th>
            <th>Transaction ID</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(payment, index) in order.payments" :key="index">
            <td>{{ index + 1 }}</td>
            <td class="text-uppercase">{{ payment.provider }}</td>
            <td><code class="small">{{ payment.transaction_id }}</code></td>
            <td>{{ formatBDT(order.total_amount) }}</td>
            <td>
              <span class="badge" :class="paymentStatusClass(payment.status)">
                {{ payment.status }}
              </span>
            </td>
            <td>{{ formatDate(payment.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="text-muted">Order not found.</p>
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
const order = ref(null)
const loading = ref(true)
const error = ref('')

function statusClass(status) {
  if (status === 'paid') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-secondary'
}

function paymentStatusClass(status) {
  if (status === 'success') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-danger'
}

function customerName(order) {
  const name = [order.user_first_name, order.user_last_name].filter(Boolean).join(' ').trim()
  return name || ''
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function loadOrder(id) {
  loading.value = true
  error.value = ''
  order.value = null
  try {
    const { data } = await $axios.get(API.orderDetail(id))
    order.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load order.'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadOrder(route.params.id))
watch(
  () => route.params.id,
  (id) => {
    if (id) loadOrder(id)
  },
)
</script>
