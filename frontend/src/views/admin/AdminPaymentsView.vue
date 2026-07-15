<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Payments</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <p v-else-if="loading" class="text-muted">Loading payments...</p>

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
              <th>Amount</th>
              <th>Provider</th>
              <th>Transaction</th>
              <th>Status</th>
              <th>Details</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="payment in payments" :key="payment.id">
              <td></td>
              <td>
                <router-link
                  class="link-primary text-decoration-underline"
                  :to="`/admin/orders/${payment.order}`"
                >
                  {{ payment.order_number }}
                </router-link>
              </td>
              <td>{{ formatBDT(payment.amount) }}</td>
              <td class="text-uppercase">{{ payment.provider }}</td>
              <td>
                <code class="small">{{ payment.transaction_id }}</code>
              </td>
              <td>
                <span class="badge" :class="statusClass(payment.status)">{{ payment.status }}</span>
              </td>
              <td>
                <router-link
                  class="link-primary text-decoration-underline"
                  :to="`/admin/payments/${payment.id}`"
                >
                  View
                </router-link>
              </td>
              <td>{{ formatDate(payment.created_at) }}</td>
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

const payments = ref([])
const loading = ref(true)
const error = ref('')
const tableKey = ref(0)

const tableOptions = {
  pageLength: 10,
  order: [[7, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { orderable: false, targets: 6 },
    { className: 'text-start', targets: '_all' },
  ],
  drawCallback: serialColumnDrawCallback(),
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
