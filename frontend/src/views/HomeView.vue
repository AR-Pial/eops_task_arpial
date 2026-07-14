<template>
  <div>
    <Navbar />

    <div class="container">
      <section class="mb-4 py-3">
        <h1 class="h3 mb-0">Welcome to E-commerce Ordering &amp; Payment System</h1>
      </section>

      <section id="products" class="pb-4">
        <h2>Products</h2>

        <div class="row">
          <div v-for="product in pageProducts" :key="product.id" class="col-md-4">
            <ProductCard :product="product" @add="onAdd" />
          </div>
        </div>

        <div class="d-flex justify-content-center align-items-center gap-2 mt-3 mb-4">
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
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import ProductCard from '../components/ProductCard.vue'
import { products as productList } from '../staticData'
import { addToCart } from '../cart'

const PAGE_SIZE = 12

const page = ref(1)
const totalPages = Math.ceil(productList.length / PAGE_SIZE) || 1

const pageProducts = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return productList.slice(start, start + PAGE_SIZE)
})

function onAdd(product) {
  addToCart(product)
  window.dispatchEvent(new Event('cart-updated'))
}
</script>
