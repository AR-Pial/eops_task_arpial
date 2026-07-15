<template>
  <StoreLayout>
    <div class="container" style="max-width: 560px">
      <h2>Payment confirmation</h2>

      <p v-if="loading" class="text-muted">Loading...</p>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else-if="order" class="card border-0 shadow-sm">
        <div class="card-body">
          <h3 class="h5 mb-3">
            <template v-if="isPaid">Payment successful</template>
            <template v-else-if="isCanceled">Payment unsuccessful</template>
            <template v-else>Payment pending</template>
          </h3>

          <p class="mb-1">
            Order No.: <strong>{{ order.number }}</strong>
          </p>
          <p class="mb-1">
            Amount: <strong>{{ formatBDT(order.total_amount) }}</strong>
          </p>
          <p class="mb-1">
            Order status:
            <span class="badge" :class="orderBadge(order.status)">{{ order.status }}</span>
          </p>

          <div v-if="payment" class="mt-3">
            <p class="mb-1">
              Payment ({{ payment.provider }}):
              <span class="badge" :class="paymentBadge(payment.status)">
                {{ payment.status }}
              </span>
            </p>
            <p v-if="payment.transaction_id" class="small text-muted mb-0">
              Transaction ID: {{ payment.transaction_id }}
            </p>
          </div>

          <div class="mt-4 d-flex flex-wrap gap-2">
            <router-link
              v-if="order.status === 'canceled'"
              class="btn btn-primary"
              :to="{ name: 'checkout', query: { order: order.id } }"
            >
              Pay again
            </router-link>
            <router-link class="btn btn-secondary" to="/orders">My orders</router-link>
            <router-link class="btn btn-outline-secondary" to="/payments">My payments</router-link>
            <router-link class="btn btn-outline-secondary" to="/">Continue shopping</router-link>
          </div>
        </div>
      </div>
    </div>
  </StoreLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StoreLayout from '../layouts/StoreLayout.vue'
import $axios from '../axios'
import API from '../apiUrls'
import { formatBDT } from '../utils/money'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const order = ref(null)

const payment = computed(() => {
  const list = order.value?.payments || []
  if (!list.length) return null
  return (
    list.find((p) => p.status === 'success') ||
    list.find((p) => p.status === 'pending') ||
    list[list.length - 1]
  )
})

const isPaid = computed(() => order.value?.status === 'paid')
const isCanceled = computed(() => order.value?.status === 'canceled')

function orderBadge(status) {
  if (status === 'paid') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-secondary'
}

function paymentBadge(status) {
  if (status === 'success') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-danger'
}

function parseApiError(err) {
  const data = err.response?.data
  if (!data) return 'Request failed'
  if (typeof data.detail === 'string') return data.detail
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return 'Request failed'
}

async function maybeConfirmPendingPayment() {
  const paymentId =
    typeof route.query.payment === 'string' ? route.query.payment : ''
  const shouldConfirm =
    route.query.confirm === '1' || route.query.confirm === 'true'
  if (!paymentId || !shouldConfirm) return

  try {
    await $axios.post(API.confirmPayment, { payment_id: paymentId })
  } catch {
    // Still load the order so the user sees current status.
  }
}

async function loadOrder(orderId) {
  const { data } = await $axios.get(API.orderDetail(orderId))
  order.value = data
}

onMounted(async () => {
  const orderId = typeof route.query.order === 'string' ? route.query.order : ''
  if (!orderId) {
    error.value = 'Missing order.'
    loading.value = false
    return
  }

  if (!localStorage.getItem('token')) {
    router.push({
      name: 'login',
      query: { next: `/confirmation?order=${orderId}` },
    })
    return
  }

  loading.value = true
  error.value = ''
  try {
    await maybeConfirmPendingPayment()
    await loadOrder(orderId)
    if (route.query.confirm || route.query.payment) {
      router.replace({ name: 'payment-confirmation', query: { order: orderId } })
    }
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
})
</script>
