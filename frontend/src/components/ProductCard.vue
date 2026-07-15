<template>
  <div class="card mb-3">
    <div class="card-body">
      <h5 class="card-title">{{ product.name }}</h5>
      <p v-if="product.category_name" class="small text-muted mb-1">{{ product.category_name }}</p>
      <p class="card-text">{{ product.description }}</p>
      <p>
        Price: {{ formatBDT(product.price) }}
        <br />
        Stock: {{ product.stock }}
      </p>
      <button
        type="button"
        class="btn btn-secondary btn-sm me-2"
        @click="$router.push({ name: 'product-detail', params: { id: product.id } })"
      >
        Details
      </button>
      <button
        type="button"
        class="btn btn-primary btn-sm"
        :disabled="product.stock < 1"
        @click="$emit('add', product)"
      >
        {{ product.stock < 1 ? 'Out of stock' : 'Add to cart' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { formatBDT } from '../utils/money'

defineProps({
  product: {
    type: Object,
    required: true,
  },
})

defineEmits(['add'])
</script>
