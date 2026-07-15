<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Order #{{ id }}</h2>

    <router-link class="btn btn-sm btn-secondary mb-3" to="/admin/orders">Back</router-link>

    <div v-if="id === '101'">
      <p>Status: <span class="badge text-bg-success">paid</span></p>
      <p>Date: 2026-07-10 14:22</p>
      <p>Total: {{ formatBDT(129.49) }}</p>
      <table class="table table-bordered">
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
          <tr>
            <td>1</td>
            <td>Wireless Headphones</td>
            <td>1</td>
            <td>{{ formatBDT(89.99) }}</td>
            <td>{{ formatBDT(89.99) }}</td>
          </tr>
          <tr>
            <td>2</td>
            <td>USB-C Hub</td>
            <td>1</td>
            <td>{{ formatBDT(39.5) }}</td>
            <td>{{ formatBDT(39.5) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="id === '102'">
      <p>Status: <span class="badge text-bg-warning">pending</span></p>
      <p>Date: 2026-07-12 09:05</p>
      <p>Total: {{ formatBDT(119) }}</p>
      <table class="table table-bordered">
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
          <tr>
            <td>1</td>
            <td>Mechanical Keyboard</td>
            <td>1</td>
            <td>{{ formatBDT(119) }}</td>
            <td>{{ formatBDT(119) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="id === '103'">
      <p>Status: <span class="badge text-bg-secondary">canceled</span></p>
      <p>Date: 2026-07-08 18:40</p>
      <p>Total: {{ formatBDT(69) }}</p>
      <table class="table table-bordered">
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
          <tr>
            <td>1</td>
            <td>Webcam HD</td>
            <td>1</td>
            <td>{{ formatBDT(69) }}</td>
            <td>{{ formatBDT(69) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="text-muted">Order not found.</p>
  </AdminLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import { formatBDT } from '../../utils/money'

const route = useRoute()
const id = computed(() => String(route.params.id))
</script>
