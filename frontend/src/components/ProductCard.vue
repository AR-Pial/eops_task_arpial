<template>
  <div class="card mb-3">
    <div class="card-body">
      <h5 class="card-title">{{ product.name }}</h5>
      <p class="card-text">{{ product.description }}</p>
      <p>
        Price: ${{ Number(product.price).toFixed(2) }}
        <br />
        Stock: {{ product.stock }}
      </p>
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
defineProps({
  product: {
    type: Object,
    required: true,
  },
})

defineEmits(['add'])
</script>
