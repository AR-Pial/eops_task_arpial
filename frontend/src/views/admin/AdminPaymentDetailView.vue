<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Payment #{{ id }}</h2>

    <router-link class="btn btn-sm btn-secondary mb-3" to="/admin/payments">Back</router-link>

    <div v-if="id === '1'">
      <p>Order: #101</p>
      <p>Provider: STRIPE</p>
      <p>Transaction: <code>pi_3MxTestAbc123</code></p>
      <p>Status: <span class="badge text-bg-success">success</span></p>
      <p>Created: 2026-07-10 14:25</p>
      <h3 class="h6 mt-3">Raw response</h3>
      <pre class="bg-light border p-3 rounded small mb-0">{
  "id": "pi_3MxTestAbc123",
  "status": "succeeded",
  "amount": 12949
}</pre>
    </div>

    <div v-else-if="id === '2'">
      <p>Order: #102</p>
      <p>Provider: BKASH</p>
      <p>Transaction: <code>TRX987654321</code></p>
      <p>Status: <span class="badge text-bg-warning">pending</span></p>
      <p>Created: 2026-07-12 09:06</p>
      <h3 class="h6 mt-3">Raw response</h3>
      <pre class="bg-light border p-3 rounded small mb-0">{
  "transactionStatus": "Initiated",
  "trxID": "TRX987654321",
  "amount": "119.00"
}</pre>
    </div>

    <div v-else-if="id === '3'">
      <p>Order: #103</p>
      <p>Provider: STRIPE</p>
      <p>Transaction: <code>pi_3MxFailXyz789</code></p>
      <p>Status: <span class="badge text-bg-danger">failed</span></p>
      <p>Created: 2026-07-08 18:41</p>
      <h3 class="h6 mt-3">Raw response</h3>
      <pre class="bg-light border p-3 rounded small mb-0">{
  "id": "pi_3MxFailXyz789",
  "status": "failed",
  "amount": 6900
}</pre>
    </div>

    <p v-else class="text-muted">Payment not found.</p>
  </AdminLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'

const route = useRoute()
const id = computed(() => String(route.params.id))
</script>
