<template>
  <StoreLayout>
    <div class="container">
      <h2>Payments</h2>

      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <p v-else-if="loading" class="text-muted">Loading payments...</p>

      <div v-else-if="selected">
        <p>
          <button type="button" class="btn btn-sm btn-secondary" @click="selected = null">
            Back
          </button>
        </p>

        <h4>Payment details</h4>
        <p>
          Status:
          <span class="badge" :class="statusClass(selected.status)">{{ selected.status }}</span>
        </p>
        <p>
          Order No.:
          <button
            type="button"
            class="btn btn-link btn-sm p-0 text-decoration-underline"
            @click="viewOrder(selected.order_number)"
          >
            {{ selected.order_number }}
          </button>
        </p>
        <p>Amount: <strong>{{ formatBDT(selected.amount) }}</strong></p>
        <p>
          Provider:
          <span class="text-uppercase">{{ selected.provider }}</span>
        </p>
        <p>
          Transaction ID:
          <code>{{ selected.transaction_id }}</code>
        </p>
        <p>Created: {{ formatDate(selected.created_at) }}</p>
        <p>Updated: {{ formatDate(selected.updated_at) }}</p>
      </div>

      <DataTable
        v-else
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
            <th>Transaction ID</th>
            <th>Status</th>
            <th>Details</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in payments" :key="payment.id">
            <td></td>
            <td>
              <button
                type="button"
                class="btn btn-link btn-sm p-0 text-decoration-underline"
                @click="viewOrder(payment.order_number)"
              >
                {{ payment.order_number }}
              </button>
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
              <button
                type="button"
                class="btn btn-sm btn-secondary"
                @click="openDetails(payment)"
              >
                Details
              </button>
            </td>
            <td>{{ formatDate(payment.created_at) }}</td>
          </tr>
        </tbody>
      </DataTable>
    </div>
  </StoreLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import StoreLayout from '../layouts/StoreLayout.vue'
import $axios from '../axios'
import API from '../apiUrls'
import { formatBDT } from '../utils/money'
import { serialColumnDrawCallback } from '../utils/dataTableSerial'

const router = useRouter()
const payments = ref([])
const selected = ref(null)
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

async function openDetails(payment) {
  error.value = ''
  try {
    const { data } = await $axios.get(API.paymentDetail(payment.id))
    selected.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load payment details.'
  }
}

function viewOrder(orderNumber) {
  if (!orderNumber) return
  router.push({ name: 'orders', query: { number: String(orderNumber) } })
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
