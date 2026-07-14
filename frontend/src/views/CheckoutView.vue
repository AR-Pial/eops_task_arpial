<template>
  <div>
    <Navbar />

    <div class="container">
      <h2>Checkout</h2>

      <div v-if="items.length === 0">
        <p>Cart is empty.</p>
        <router-link to="/">Go to products</router-link>
      </div>

      <div v-else>
        <table class="table table-bordered">
          <thead>
            <tr>
              <th>Product</th>
              <th>Price</th>
              <th>Qty</th>
              <th>Subtotal</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.product_id">
              <td>{{ item.name }}</td>
              <td>${{ Number(item.price).toFixed(2) }}</td>
              <td style="width: 100px">
                <input
                  v-model.number="item.quantity"
                  type="number"
                  min="1"
                  class="form-control form-control-sm"
                  @change="onQty(item)"
                />
              </td>
              <td>${{ (item.price * item.quantity).toFixed(2) }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-danger" @click="onRemove(item.product_id)">
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <p><b>Total: ${{ total.toFixed(2) }}</b></p>

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

        <p v-if="info" class="text-success">{{ info }}</p>
        <p v-if="error" class="text-danger">{{ error }}</p>

        <button type="button" class="btn btn-primary" :disabled="loading" @click="placeOrder">
          {{ loading ? 'Please wait...' : 'Place order' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import { cartTotal, clearCart, getCart, removeFromCart, updateQty } from '../cart'

const router = useRouter()
const items = ref(getCart())
const provider = ref('stripe')
const loading = ref(false)
const info = ref('')
const error = ref('')

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

function placeOrder() {
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

  setTimeout(() => {
    clearCart()
    refresh()
    info.value =
      'Order created (static). Provider: ' + provider.value + '. Check My Orders page.'
    loading.value = false
    setTimeout(() => {
      router.push({ name: 'orders' })
    }, 1000)
  }, 500)
}
</script>
