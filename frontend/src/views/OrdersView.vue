<template>
  <StoreLayout>
    <div class="container">
      <h2>My Orders</h2>

      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <p v-else-if="loading" class="text-muted">Loading orders...</p>

      <div v-else-if="selected">
        <p>
          <button type="button" class="btn btn-sm btn-secondary" @click="selected = null">
            Back
          </button>
        </p>

        <h4>Order No. {{ selected.number }}</h4>
        <p>
          Status:
          <span class="badge" :class="statusClass(selected.status)">{{ selected.status }}</span>
        </p>
        <p>Date: {{ formatDate(selected.created_at) }}</p>
        <p>Total: <strong>{{ formatBDT(selected.total_amount) }}</strong></p>

        <div v-if="selected.status === 'pending'" class="alert alert-warning py-2">
          Payment is not completed yet.
          <div class="mt-2">
            <button
              type="button"
              class="btn btn-sm btn-outline-danger"
              :disabled="canceling"
              @click="cancelOrder(selected)"
            >
              {{ canceling ? 'Canceling...' : 'Cancel order' }}
            </button>
          </div>
        </div>
        <div v-else-if="selected.status === 'canceled'" class="alert alert-secondary py-2">
          This order was canceled.
          <div class="mt-2">
            <button type="button" class="btn btn-sm btn-primary" @click="payAgain(selected)">
              Pay again
            </button>
          </div>
        </div>

        <h5 class="h6 mt-4">Items</h5>
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
            <tr v-for="(item, index) in selected.items" :key="index">
              <td>{{ index + 1 }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ formatBDT(item.price) }}</td>
              <td>{{ formatBDT(item.subtotal) }}</td>
            </tr>
          </tbody>
        </table>

        <h5 class="h6 mt-4">Payments</h5>
        <p v-if="!selected.payments?.length" class="text-muted small">No payments for this order.</p>
        <table v-else class="table table-bordered">
          <thead>
            <tr>
              <th>#</th>
              <th>Provider</th>
              <th>Transaction</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(payment, index) in selected.payments" :key="index">
              <td>{{ index + 1 }}</td>
              <td class="text-uppercase">{{ payment.provider }}</td>
              <td><code class="small">{{ payment.transaction_id }}</code></td>
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
            <th>Total Amount</th>
            <th>Status</th>
            <th>Details</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td></td>
            <td>
              <button
                type="button"
                class="btn btn-link btn-sm p-0 text-decoration-underline"
                @click="openDetails(order)"
              >
                {{ order.number }}
              </button>
            </td>
            <td>{{ formatBDT(order.total_amount) }}</td>
            <td>
              <span class="badge" :class="statusClass(order.status)">{{ order.status }}</span>
            </td>
            <td>
              <button type="button" class="btn btn-sm btn-secondary me-1" @click="openDetails(order)">
                Details
              </button>
              <button
                v-if="order.status === 'canceled'"
                type="button"
                class="btn btn-sm btn-primary me-1"
                @click="payAgain(order)"
              >
                Pay again
              </button>
              <button
                v-if="order.status === 'pending'"
                type="button"
                class="btn btn-sm btn-outline-danger"
                :disabled="canceling"
                @click="cancelOrder(order)"
              >
                Cancel
              </button>
            </td>
            <td>{{ formatDate(order.created_at) }}</td>
          </tr>
        </tbody>
      </DataTable>
    </div>
  </StoreLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StoreLayout from '../layouts/StoreLayout.vue'
import $axios from '../axios'
import API from '../apiUrls'
import { formatBDT } from '../utils/money'
import { serialColumnDrawCallback } from '../utils/dataTableSerial'

const route = useRoute()
const router = useRouter()
const orders = ref([])
const selected = ref(null)
const loading = ref(true)
const canceling = ref(false)
const error = ref('')
const tableKey = ref(0)

const tableOptions = {
  pageLength: 10,
  order: [[5, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { orderable: false, targets: 4 },
    { className: 'text-start', targets: '_all' },
  ],
  drawCallback: serialColumnDrawCallback(),
}

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

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function openDetails(order) {
  error.value = ''
  try {
    const { data } = await $axios.get(API.orderDetail(order.id))
    selected.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load order details.'
  }
}

function payAgain(order) {
  if (!order?.id) return
  router.push({ name: 'checkout', query: { order: order.id } })
}

async function cancelOrder(order) {
  if (!window.confirm('Cancel this pending order? You can place a new order later.')) return
  canceling.value = true
  error.value = ''
  try {
    const { data } = await $axios.post(API.orderCancel(order.id))
    const idx = orders.value.findIndex((o) => o.id === order.id)
    if (idx !== -1) orders.value[idx] = data
    if (selected.value?.id === order.id) selected.value = data
    tableKey.value += 1
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not cancel order.'
  } finally {
    canceling.value = false
  }
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await $axios.get(API.orders)
    orders.value = Array.isArray(data) ? data : data.results || []
    tableKey.value += 1

    const num = route.query.number
    if (num) {
      const match = orders.value.find((o) => String(o.number) === String(num))
      if (match) {
        await openDetails(match)
        router.replace({ name: 'orders' })
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load orders.'
  } finally {
    loading.value = false
  }
})
</script>
