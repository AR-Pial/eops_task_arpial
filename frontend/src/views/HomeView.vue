<template>
  <StoreLayout>
    <div class="container">
      <section class="mb-4">
        <h1 class="h3 mb-0">Welcome to E-commerce Ordering &amp; Payment System</h1>
      </section>

      <section id="products">
        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <h2 class="mb-0">Products</h2>
          <div class="d-flex align-items-center gap-2">
            <label class="form-label mb-0 small text-muted" for="categoryFilter">Category</label>
            <select
              id="categoryFilter"
              v-model="selectedCategory"
              class="form-select form-select-sm"
              style="min-width: 200px"
              @change="onCategoryChange"
            >
              <option value="">All categories</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ categoryLabel(cat) }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>
        <p v-else-if="loading" class="text-muted">Loading products...</p>
        <p v-else-if="!productList.length" class="text-muted">No products available.</p>

        <div v-else class="row">
          <div v-for="product in pageProducts" :key="product.id" class="col-md-4">
            <ProductCard :product="product" @add="onAdd" />
          </div>
        </div>

        <div
          v-if="!loading && productList.length"
          class="d-flex justify-content-center align-items-center gap-2 mt-3"
        >
          <button
            type="button"
            class="btn btn-outline-secondary"
            :disabled="page <= 1"
            @click="page--"
          >
            Previous
          </button>
          <button
            v-for="n in totalPages"
            :key="n"
            type="button"
            class="btn"
            :class="n === page ? 'btn-secondary' : 'btn-outline-secondary'"
            @click="page = n"
          >
            {{ n }}
          </button>
          <button
            type="button"
            class="btn btn-outline-secondary"
            :disabled="page >= totalPages"
            @click="page++"
          >
            Next
          </button>
        </div>
      </section>
    </div>
  </StoreLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import StoreLayout from '../layouts/StoreLayout.vue'
import ProductCard from '../components/ProductCard.vue'
import { addToCart } from '../cart'
import { showToast } from '../toast'
import $axios from '../axios'
import API from '../apiUrls'

const PAGE_SIZE = 12

const page = ref(1)
const productList = ref([])
const categories = ref([])
const selectedCategory = ref('')
const loading = ref(true)
const error = ref('')

const totalPages = computed(() => Math.ceil(productList.value.length / PAGE_SIZE) || 1)

const pageProducts = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return productList.value.slice(start, start + PAGE_SIZE)
})

function categoryLabel(cat) {
  if (!cat.parent) return cat.name
  const parent = categories.value.find((c) => c.id === cat.parent)
  return parent ? `${parent.name} / ${cat.name}` : cat.name
}

async function loadCategories() {
  const { data } = await $axios.get(API.categories)
  categories.value = Array.isArray(data) ? data : data.results || []
}

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (selectedCategory.value) {
      params.category = selectedCategory.value
      params.include_descendants = 1
    }
    const { data } = await $axios.get(API.products, { params })
    productList.value = Array.isArray(data) ? data : data.results || []
    page.value = 1
  } catch (err) {
    error.value =
      err.response?.data?.detail ||
      'Could not load products. Please try again.'
  } finally {
    loading.value = false
  }
}

function onCategoryChange() {
  loadProducts()
}

function onAdd(product) {
  addToCart(product)
  window.dispatchEvent(new Event('cart-updated'))
  showToast(`Added "${product.name}" to cart`)
}

onMounted(async () => {
  try {
    await loadCategories()
  } catch {
    categories.value = []
  }
  await loadProducts()
})
</script>
