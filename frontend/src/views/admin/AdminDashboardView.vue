<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Dashboard</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <p v-else-if="loading" class="text-muted">Loading...</p>

    <div v-else class="row g-3">
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Products</div>
            <div class="fs-4 fw-semibold">{{ stats.products }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Orders</div>
            <div class="fs-4 fw-semibold">{{ stats.orders }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Payments</div>
            <div class="fs-4 fw-semibold">{{ stats.payments }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Revenue</div>
            <div class="fs-4 fw-semibold">{{ formatBDT(stats.revenue) }}</div>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import $axios from '../../axios'
import API from '../../apiUrls'
import { formatBDT } from '../../utils/money'

const loading = ref(true)
const error = ref('')
const stats = reactive({
  products: 0,
  orders: 0,
  payments: 0,
  revenue: 0,
})

function listFrom(data) {
  return Array.isArray(data) ? data : data?.results || []
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const [productsRes, ordersRes, paymentsRes] = await Promise.all([
      $axios.get(API.products),
      $axios.get(API.orders),
      $axios.get(API.payments),
    ])
    const products = listFrom(productsRes.data)
    const orders = listFrom(ordersRes.data)
    const payments = listFrom(paymentsRes.data)

    stats.products = products.length
    stats.orders = orders.length
    stats.payments = payments.length
    stats.revenue = orders
      .filter((o) => o.status === 'paid')
      .reduce((sum, o) => sum + Number(o.total_amount || 0), 0)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load dashboard.'
  } finally {
    loading.value = false
  }
})
</script>
