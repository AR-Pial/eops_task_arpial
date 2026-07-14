<template>
  <div>
    <Navbar />

    <div class="container py-3">
      <h2>My Orders</h2>

      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <p v-else-if="loading" class="text-muted">Loading orders...</p>

      <div v-else-if="selected">
        <p>
          <button type="button" class="btn btn-sm btn-secondary" @click="selected = null">
            Back
          </button>
        </p>
        <h4>Order details</h4>
        <p>
          Status:
          <span class="badge" :class="statusClass(selected.status)">{{ selected.status }}</span>
        </p>
        <p>Date: {{ formatDate(selected.created_at) }}</p>
        <p>Total: {{ Number(selected.total_amount).toFixed(2) }}</p>

        <table class="table table-bordered">
          <thead>
            <tr>
              <th>#</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in selected.items" :key="item.id">
              <td>{{ index + 1 }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ Number(item.price).toFixed(2) }}</td>
              <td>{{ Number(item.subtotal).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <DataTable
        v-else
        :key="tableKey"
        class="table table-striped table-hover align-middle w-100"
        :options="tableOptions"
      >
        <thead>
          <tr>
            <th>#</th>
            <th>Total Amount</th>
            <th>Status</th>
            <th>Details</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(order, index) in orders" :key="order.id">
            <td>{{ index + 1 }}</td>
            <td>{{ Number(order.total_amount).toFixed(2) }}</td>
            <td>
              <span class="badge" :class="statusClass(order.status)">{{ order.status }}</span>
            </td>
            <td>
              <button type="button" class="btn btn-sm btn-secondary" @click="selected = order">
                Details
              </button>
            </td>
            <td>{{ formatDate(order.created_at) }}</td>
          </tr>
        </tbody>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import $axios from '../axios'
import API from '../apiUrls'

const orders = ref([])
const selected = ref(null)
const loading = ref(true)
const error = ref('')
const tableKey = ref(0)

const tableOptions = {
  pageLength: 10,
  order: [[4, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { orderable: false, targets: 3 },
    { className: 'text-start', targets: '_all' },
  ],
}

function statusClass(status) {
  if (status === 'paid') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-secondary'
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await $axios.get(API.orders)
    orders.value = Array.isArray(data) ? data : data.results || []
    tableKey.value += 1
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load orders.'
  } finally {
    loading.value = false
  }
})
</script>
