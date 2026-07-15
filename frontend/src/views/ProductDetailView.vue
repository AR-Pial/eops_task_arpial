<template>
  <StoreLayout>
    <div class="container">
      <router-link class="btn btn-sm btn-secondary mb-3" to="/#products">Back to products</router-link>

      <p v-if="loading" class="text-muted">Loading...</p>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else-if="product">
        <h1 class="h3 mb-3">{{ product.name }}</h1>

        <p v-if="product.category_name" class="text-muted mb-1">{{ product.category_name }}</p>
        <p class="text-muted mb-1">SKU: {{ product.sku }}</p>
        <p class="mb-3">{{ product.description }}</p>

        <p>
          Price: <strong>{{ formatBDT(product.price) }}</strong>
        </p>
        <p>
          Stock:
          <span v-if="product.stock < 1" class="badge text-bg-secondary">Out of stock</span>
          <span v-else>{{ product.stock }} available</span>
        </p>

        <button
          type="button"
          class="btn btn-primary"
          :disabled="product.stock < 1"
          @click="onAdd"
        >
          {{ product.stock < 1 ? 'Out of stock' : 'Add to cart' }}
        </button>

        <section v-if="related.length" class="mt-5">
          <h2 class="h5">Related products</h2>
          <div class="row">
            <div v-for="item in related" :key="item.id" class="col-md-4">
              <ProductCard :product="item" @add="onAddRelated" />
            </div>
          </div>
        </section>
      </div>

      <p v-else class="text-muted">Product not found.</p>
    </div>
  </StoreLayout>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import StoreLayout from '../layouts/StoreLayout.vue'
import ProductCard from '../components/ProductCard.vue'
import { addToCart } from '../cart'
import $axios from '../axios'
import API from '../apiUrls'
import { formatBDT } from '../utils/money'

const route = useRoute()
const product = ref(null)
const related = ref([])
const loading = ref(true)
const error = ref('')

async function loadProduct(id) {
  loading.value = true
  error.value = ''
  product.value = null
  related.value = []
  try {
    const { data } = await $axios.get(API.productDetail(id))
    product.value = data
    try {
      const relatedRes = await $axios.get(API.productRelated(id))
      related.value = Array.isArray(relatedRes.data) ? relatedRes.data : []
    } catch {
      related.value = []
    }
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = ''
      product.value = null
    } else {
      error.value = err.response?.data?.detail || 'Could not load product.'
    }
  } finally {
    loading.value = false
  }
}

function onAdd() {
  if (!product.value || product.value.stock < 1) return
  addToCart(product.value)
  window.dispatchEvent(new Event('cart-updated'))
}

function onAddRelated(item) {
  addToCart(item)
  window.dispatchEvent(new Event('cart-updated'))
}

onMounted(() => loadProduct(route.params.id))
watch(
  () => route.params.id,
  (id) => {
    if (id) loadProduct(id)
  },
)
</script>
