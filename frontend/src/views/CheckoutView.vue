<template>
  <StoreLayout>
    <div class="container">
      <h2>{{ payingExisting ? 'Pay again' : 'Checkout' }}</h2>

      <p v-if="loadingOrder" class="text-muted">Loading order...</p>

      <div v-else-if="!payingExisting && items.length === 0 && !orderResult">
        <p>Cart is empty.</p>
        <router-link to="/">Go to products</router-link>
      </div>

      <div v-else-if="!orderResult || (payingExisting && !paymentResult && canRetryPay)">
        <template v-if="payingExisting && orderResult">
          <p class="mb-1">
            Order No.: <strong>{{ orderResult.number }}</strong>
          </p>
          <p class="mb-3">
            Amount: <strong>{{ formatBDT(orderResult.total_amount) }}</strong>
          </p>
          <table v-if="orderResult.items?.length" class="table table-bordered">
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
              <tr v-for="(item, index) in orderResult.items" :key="index">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ formatBDT(item.price) }}</td>
                <td>{{ formatBDT(item.subtotal) }}</td>
              </tr>
            </tbody>
          </table>
        </template>

        <template v-else>
          <table class="table table-bordered">
            <thead>
              <tr>
                <th>#</th>
                <th>Product</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in items" :key="item.product_id">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ formatBDT(item.price) }}</td>
                <td style="width: 100px">
                  <input
                    v-model.number="item.quantity"
                    type="number"
                    min="1"
                    class="form-control form-control-sm"
                    @change="onQty(item)"
                  />
                </td>
                <td>{{ formatBDT(item.price * item.quantity) }}</td>
                <td>
                  <button type="button" class="btn btn-sm btn-danger" @click="onRemove(item.product_id)">
                    Remove
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <p><b>Total: {{ formatBDT(total) }}</b></p>
        </template>

        <div class="mb-3">
          <label class="form-label">Payment provider</label>
          <div>
            <div class="form-check">
              <input
                id="stripe"
                v-model="provider"
                class="form-check-input"
                type="radio"
                value="stripe"
              />
              <label class="form-check-label" for="stripe">Stripe</label>
            </div>
            <div class="form-check">
              <input
                id="bkash"
                v-model="provider"
                class="form-check-input"
                type="radio"
                value="bkash"
              />
              <label class="form-check-label" for="bkash">bKash</label>
            </div>
          </div>
        </div>

        <p v-if="error" class="text-danger">{{ error }}</p>

        <button
          type="button"
          class="btn btn-primary"
          :disabled="loading"
          @click="payingExisting ? payAgain() : placeOrder()"
        >
          {{
            loading
              ? 'Please wait...'
              : payingExisting
                ? 'Pay again'
                : 'Place order & pay'
          }}
        </button>

        <router-link v-if="payingExisting" class="btn btn-outline-secondary ms-2" to="/orders">
          Back to orders
        </router-link>
      </div>

      <div v-else class="card border-0 shadow-sm">
        <div class="card-body">
          <h3 class="h5">{{ payingExisting ? 'Payment' : 'Order placed' }}</h3>
          <p class="mb-1">Order No.: <strong>{{ orderResult.number }}</strong></p>
          <p class="mb-1">
            Amount: <strong>{{ formatBDT(orderResult.total_amount) }}</strong>
          </p>
          <p class="mb-1">
            Order status:
            <span class="badge" :class="orderBadge(orderResult.status)">
              {{ orderResult.status }}
            </span>
          </p>

          <div v-if="paymentResult" class="mt-3">
            <p class="mb-1">
              Payment ({{ paymentResult.provider }}):
              <span class="badge" :class="paymentBadge(paymentResult.status)">
                {{ paymentResult.status }}
              </span>
            </p>
            <p class="small text-muted mb-2">
              Transaction: {{ paymentResult.transaction_id }}
            </p>

            <div v-if="showStripeForm" class="mb-3">
              <div ref="stripeMountEl" class="border rounded p-3 bg-white mb-3"></div>
              <button
                type="button"
                class="btn btn-success me-2"
                :disabled="confirming || !stripeReady"
                @click="payWithStripe"
              >
                {{ confirming ? 'Processing...' : 'Pay now' }}
              </button>
            </div>

            <button
              v-if="paymentResult.mock && paymentResult.status === 'pending'"
              type="button"
              class="btn btn-success me-2"
              :disabled="confirming"
              @click="confirmPayment"
            >
              {{ confirming ? 'Confirming...' : 'Confirm payment' }}
            </button>
          </div>

          <p v-if="info" class="text-success mt-3">{{ info }}</p>
          <p v-if="error" class="text-danger mt-3">{{ error }}</p>

          <div v-if="orderResult.status === 'canceled'" class="mt-3">
            <button type="button" class="btn btn-primary me-2" @click="resetForPayAgain">
              Pay again
            </button>
          </div>

          <div class="mt-3 d-flex gap-2">
            <router-link class="btn btn-secondary" to="/orders">My orders</router-link>
            <router-link class="btn btn-outline-secondary" to="/payments">My payments</router-link>
          </div>
        </div>
      </div>
    </div>
  </StoreLayout>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'
import StoreLayout from '../layouts/StoreLayout.vue'
import { cartTotal, clearCart, getCart, removeFromCart, updateQty } from '../cart'
import $axios from '../axios'
import API from '../apiUrls'
import { formatBDT } from '../utils/money'

const route = useRoute()
const router = useRouter()
const items = ref(getCart())
const provider = ref('stripe')
const loading = ref(false)
const loadingOrder = ref(false)
const confirming = ref(false)
const stripeReady = ref(false)
const info = ref('')
const error = ref('')
const orderResult = ref(null)
const paymentResult = ref(null)
const payingExisting = ref(false)
const stripeMountEl = ref(null)

let stripe = null
let elements = null
let paymentElement = null

const total = computed(() => cartTotal(items.value))

const canRetryPay = computed(
  () => orderResult.value && orderResult.value.status === 'canceled',
)

const showStripeForm = computed(
  () =>
    paymentResult.value &&
    !paymentResult.value.mock &&
    paymentResult.value.provider === 'stripe' &&
    paymentResult.value.status === 'pending' &&
    paymentResult.value.client_secret,
)

function refresh() {
  items.value = getCart()
  window.dispatchEvent(new Event('cart-updated'))
}

function onQty(item) {
  updateQty(item.product_id, item.quantity)
  refresh()
}

function onRemove(productId) {
  removeFromCart(productId)
  refresh()
}

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
  if (Array.isArray(data.items)) return data.items[0]
  if (typeof data.items === 'string') return data.items
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return 'Request failed'
}

function teardownStripe() {
  if (paymentElement) {
    paymentElement.unmount()
    paymentElement = null
  }
  elements = null
  stripe = null
  stripeReady.value = false
}

async function mountStripeForm(clientSecret) {
  teardownStripe()
  const pk = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
  if (!pk) {
    error.value = 'Card payments are unavailable right now.'
    return
  }

  await nextTick()
  if (!stripeMountEl.value) return

  stripe = await loadStripe(pk)
  if (!stripe) {
    error.value = 'Could not load the card form.'
    return
  }

  elements = stripe.elements({ clientSecret })
  paymentElement = elements.create('payment')
  paymentElement.mount(stripeMountEl.value)
  stripeReady.value = true
}

async function startPayment(order) {
  orderResult.value = { ...order }
  const { data: payment } = await $axios.post(API.checkout, {
    order_id: order.id,
    provider: provider.value,
  })
  paymentResult.value = payment

  if (payment.status === 'success') {
    info.value = 'Payment successful.'
    orderResult.value = { ...order, status: 'paid' }
  } else if (payment.mock) {
    info.value = payingExisting.value
      ? 'Confirm payment to finish.'
      : 'Order placed. Confirm payment to finish.'
    orderResult.value = { ...order, status: 'pending' }
  } else if (payment.provider === 'stripe' && payment.client_secret) {
    orderResult.value = { ...order, status: 'pending' }
    await mountStripeForm(payment.client_secret)
  } else if (payment.redirect_url) {
    orderResult.value = { ...order, status: 'pending' }
    info.value = 'Redirecting...'
    window.location.href = payment.redirect_url
  } else {
    orderResult.value = { ...order, status: 'pending' }
    info.value = 'Waiting for payment confirmation.'
  }
}

async function placeOrder() {
  if (!localStorage.getItem('token')) {
    router.push({ name: 'login', query: { next: '/checkout' } })
    return
  }

  if (!provider.value) {
    error.value = 'Select a payment provider'
    return
  }

  loading.value = true
  error.value = ''
  info.value = ''

  try {
    const orderPayload = {
      items: items.value.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
      })),
    }
    const { data: order } = await $axios.post(API.orders, orderPayload)
    await startPayment(order)
    clearCart()
    refresh()
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

async function payAgain() {
  if (!localStorage.getItem('token')) {
    router.push({
      name: 'login',
      query: { next: `/checkout?order=${route.query.order || orderResult.value?.id}` },
    })
    return
  }

  if (!orderResult.value?.id) {
    error.value = 'Order not found.'
    return
  }

  if (!provider.value) {
    error.value = 'Select a payment provider'
    return
  }

  loading.value = true
  error.value = ''
  info.value = ''
  paymentResult.value = null

  try {
    await startPayment(orderResult.value)
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

function resetForPayAgain() {
  paymentResult.value = null
  info.value = ''
  error.value = ''
  teardownStripe()
  payingExisting.value = true
}

async function payWithStripe() {
  if (!stripe || !elements || !paymentResult.value?.id) return

  confirming.value = true
  error.value = ''
  try {
    const { error: stripeError, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
      confirmParams: {
        return_url: `${window.location.origin}/checkout`,
      },
    })

    if (stripeError) {
      error.value = stripeError.message || 'Card payment failed'
      if (stripeError.type === 'card_error' || stripeError.type === 'invalid_request_error') {
        await confirmPayment({ silentPending: true })
      }
      return
    }

    if (paymentIntent?.status === 'succeeded') {
      await confirmPayment()
      teardownStripe()
    } else {
      info.value = 'Confirming payment...'
      await confirmPayment()
    }
  } catch (err) {
    error.value = err.message || 'Stripe payment failed'
  } finally {
    confirming.value = false
  }
}

async function confirmPayment({ silentPending = false } = {}) {
  if (!paymentResult.value?.id) return
  confirming.value = true
  if (!silentPending) error.value = ''
  try {
    const { data } = await $axios.post(API.confirmPayment, {
      payment_id: paymentResult.value.id,
    })
    paymentResult.value = { ...paymentResult.value, ...data }
    if (data.status === 'success') {
      info.value = 'Payment successful.'
      error.value = ''
      if (orderResult.value) {
        orderResult.value = { ...orderResult.value, status: 'paid' }
      }
      teardownStripe()
    } else if (data.status === 'failed') {
      info.value = ''
      error.value = 'Payment failed. This order has been canceled.'
      if (orderResult.value) {
        orderResult.value = { ...orderResult.value, status: 'canceled' }
      }
      teardownStripe()
    } else if (!silentPending) {
      info.value = 'Payment is still pending.'
    }
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    confirming.value = false
  }
}

async function handleBkashReturn(paymentID, callbackStatus) {
  if (!localStorage.getItem('token')) {
    router.push({
      name: 'login',
      query: { next: `/checkout?paymentID=${paymentID}&status=${callbackStatus}` },
    })
    return
  }

  loadingOrder.value = true
  confirming.value = true
  error.value = ''
  info.value = 'Confirming payment...'
  payingExisting.value = false

  try {
    const payload = {
      transaction_id: paymentID,
      callback_status: callbackStatus === 'success' ? 'success' : callbackStatus,
    }
    const { data } = await $axios.post(API.confirmPayment, payload)
    paymentResult.value = data
    orderResult.value = {
      id: data.order,
      number: data.order_number,
      total_amount: data.amount,
      status: data.order_status || (data.status === 'success' ? 'paid' : 'canceled'),
    }

    if (data.status === 'success') {
      info.value = 'Payment successful.'
    } else if (data.status === 'failed') {
      info.value = ''
      error.value =
        callbackStatus === 'cancel'
          ? 'Payment was cancelled.'
          : 'Payment failed. This order has been canceled.'
    } else {
      info.value = 'Payment is still pending.'
    }

    router.replace({ name: 'checkout' })
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loadingOrder.value = false
    confirming.value = false
  }
}

onMounted(async () => {
  const paymentID =
    typeof route.query.paymentID === 'string' ? route.query.paymentID : ''
  const bkashStatus =
    typeof route.query.status === 'string' ? route.query.status.toLowerCase() : ''

  if (paymentID && ['success', 'failure', 'cancel'].includes(bkashStatus)) {
    await handleBkashReturn(paymentID, bkashStatus)
    return
  }

  const orderId = typeof route.query.order === 'string' ? route.query.order : ''
  if (!orderId) return

  if (!localStorage.getItem('token')) {
    router.push({ name: 'login', query: { next: `/checkout?order=${orderId}` } })
    return
  }

  loadingOrder.value = true
  error.value = ''
  payingExisting.value = true
  try {
    const { data } = await $axios.get(API.orderDetail(orderId))
    if (data.status === 'paid') {
      error.value = 'This order is already paid.'
      orderResult.value = data
      payingExisting.value = false
      return
    }
    if (data.status !== 'canceled') {
      error.value = 'Only canceled orders can be paid again.'
      payingExisting.value = false
      return
    }
    orderResult.value = data
  } catch (err) {
    error.value = parseApiError(err)
    payingExisting.value = false
  } finally {
    loadingOrder.value = false
  }
})

onBeforeUnmount(() => {
  teardownStripe()
})
</script>
