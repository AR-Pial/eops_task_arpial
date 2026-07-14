<template>
  <div>
    <Navbar />

    <div class="container py-3">
      <h2>Checkout</h2>

      <div v-if="items.length === 0 && !orderResult">
        <p>Cart is empty.</p>
        <router-link to="/">Go to products</router-link>
      </div>

      <div v-else-if="!orderResult">
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
              <td>{{ Number(item.price).toFixed(2) }}</td>
              <td style="width: 100px">
                <input
                  v-model.number="item.quantity"
                  type="number"
                  min="1"
                  class="form-control form-control-sm"
                  @change="onQty(item)"
                />
              </td>
              <td>{{ (item.price * item.quantity).toFixed(2) }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-danger" @click="onRemove(item.product_id)">
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <p><b>Total: {{ total.toFixed(2) }}</b></p>

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

        <button type="button" class="btn btn-primary" :disabled="loading" @click="placeOrder">
          {{ loading ? 'Please wait...' : 'Place order & pay' }}
        </button>
      </div>

      <div v-else class="card border-0 shadow-sm">
        <div class="card-body">
          <h3 class="h5">Order placed</h3>
          <p class="mb-1">Order ID: <code>{{ orderResult.id }}</code></p>
          <p class="mb-1">
            Amount: <strong>{{ Number(orderResult.total_amount).toFixed(2) }}</strong>
          </p>
          <p class="mb-1">
            Order status:
            <span class="badge text-bg-warning">{{ orderResult.status }}</span>
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

            <div v-if="paymentResult.mock && paymentResult.status === 'pending'" class="alert alert-info">
              Provider keys are not configured — using sandbox mock. Click confirm to complete payment
              and reduce stock.
            </div>

            <button
              v-if="paymentResult.status === 'pending'"
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

          <div class="mt-3 d-flex gap-2">
            <router-link class="btn btn-secondary" to="/orders">My orders</router-link>
            <router-link class="btn btn-outline-secondary" to="/payments">My payments</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import { cartTotal, clearCart, getCart, removeFromCart, updateQty } from '../cart'
import $axios from '../axios'
import API from '../apiUrls'

const router = useRouter()
const items = ref(getCart())
const provider = ref('stripe')
const loading = ref(false)
const confirming = ref(false)
const info = ref('')
const error = ref('')
const orderResult = ref(null)
const paymentResult = ref(null)

const total = computed(() => cartTotal(items.value))

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
    orderResult.value = order

    const { data: payment } = await $axios.post(API.checkout, {
      order_id: order.id,
      provider: provider.value,
    })
    paymentResult.value = payment

    clearCart()
    refresh()

    if (payment.status === 'success') {
      info.value = 'Payment successful. Stock updated.'
      orderResult.value = { ...order, status: 'paid' }
    } else if (payment.mock) {
      info.value = 'Order created. Confirm mock payment to finish.'
    } else {
      info.value = 'Payment initiated. Confirm or wait for provider webhook.'
    }
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

async function confirmPayment() {
  if (!paymentResult.value?.id) return
  confirming.value = true
  error.value = ''
  try {
    const { data } = await $axios.post(API.confirmPayment, {
      payment_id: paymentResult.value.id,
    })
    paymentResult.value = { ...paymentResult.value, ...data }
    if (data.status === 'success') {
      info.value = 'Payment confirmed. Order paid and stock reduced.'
      if (orderResult.value) {
        orderResult.value = { ...orderResult.value, status: 'paid' }
      }
    }
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    confirming.value = false
  }
}
</script>
