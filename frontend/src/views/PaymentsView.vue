<template>
  <div>
    <Navbar />

    <div class="container py-3">
      <h2>Payments</h2>

      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <p v-else-if="loading" class="text-muted">Loading payments...</p>

      <DataTable
        v-else
        :key="tableKey"
        class="table table-striped table-hover align-middle w-100"
        :options="tableOptions"
      >
        <thead>
          <tr>
            <th>#</th>
            <th>Provider</th>
            <th>Transaction ID</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(payment, index) in payments" :key="payment.id">
            <td>{{ index + 1 }}</td>
            <td class="text-uppercase">{{ payment.provider }}</td>
            <td>{{ payment.transaction_id }}</td>
            <td>
              <span class="badge" :class="statusClass(payment.status)">{{ payment.status }}</span>
            </td>
            <td>{{ formatDate(payment.created_at) }}</td>
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

const payments = ref([])
const loading = ref(true)
const error = ref('')
const tableKey = ref(0)

const tableOptions = {
  pageLength: 10,
  order: [[4, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { className: 'text-start', targets: '_all' },
  ],
}

function statusClass(status) {
  if (status === 'success') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-danger'
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await $axios.get(API.payments)
    payments.value = Array.isArray(data) ? data : data.results || []
    tableKey.value += 1
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load payments.'
  } finally {
    loading.value = false
  }
})
</script>
