<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Orders</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <p v-else-if="loading" class="text-muted">Loading orders...</p>

    <div v-else class="card border-0 shadow-sm">
      <div class="card-body">
        <DataTable
          :key="tableKey"
          class="table table-striped table-hover align-middle w-100"
          :options="tableOptions"
        >
          <thead>
            <tr>
              <th>Serial</th>
              <th>Order No.</th>
              <th>Customer</th>
              <th>Total</th>
              <th>Status</th>
              <th>Details</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.id">
              <td></td>
              <td>
                <router-link
                  class="link-primary text-decoration-underline"
                  :to="`/admin/orders/${order.id}`"
                >
                  {{ order.number }}
                </router-link>
              </td>
              <td>{{ order.user_email || '—' }}</td>
              <td>{{ formatBDT(order.total_amount) }}</td>
              <td>
                <span class="badge" :class="statusClass(order.status)">{{ order.status }}</span>
              </td>
              <td>
                <router-link
                  class="link-primary text-decoration-underline"
                  :to="`/admin/orders/${order.id}`"
                >
                  View
                </router-link>
              </td>
              <td>{{ formatDate(order.created_at) }}</td>
            </tr>
          </tbody>
        </DataTable>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import $axios from '../../axios'
import API from '../../apiUrls'
import { formatBDT } from '../../utils/money'
import { serialColumnDrawCallback } from '../../utils/dataTableSerial'

const orders = ref([])
const loading = ref(true)
const error = ref('')
const tableKey = ref(0)

const tableOptions = {
  pageLength: 10,
  order: [[6, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { orderable: false, targets: 5 },
    { className: 'text-start', targets: '_all' },
  ],
  drawCallback: serialColumnDrawCallback(),
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
