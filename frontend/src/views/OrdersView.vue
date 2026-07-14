<template>
  <div>
    <Navbar />

    <div class="container">
      <h2>My Orders</h2>

      <div v-if="selected">
        <p>
          <button type="button" class="btn btn-sm btn-secondary" @click="selected = null">
            Back
          </button>
        </p>
        <h4>Order #{{ selected.id }}</h4>
        <p>
          Status:
          <span class="badge" :class="statusClass(selected.status)">{{ selected.status }}</span>
        </p>
        <p>Date: {{ selected.created_at }}</p>
        <p>Total: ${{ Number(selected.total_amount).toFixed(2) }}</p>

        <table class="table table-bordered">
          <thead>
            <tr>
              <th>Product</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in selected.items" :key="index">
              <td>{{ item.name }}</td>
              <td>{{ item.quantity }}</td>
              <td>${{ Number(item.price).toFixed(2) }}</td>
              <td>${{ Number(item.subtotal).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <DataTable
        v-else
        class="table table-striped table-hover align-middle w-100"
        :options="tableOptions"
      >
        <thead>
          <tr>
            <th>ID</th>
            <th>Total</th>
            <th>Status</th>
            <th>Details</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td>#{{ order.id }}</td>
            <td>${{ Number(order.total_amount).toFixed(2) }}</td>
            <td>
              <span class="badge" :class="statusClass(order.status)">{{ order.status }}</span>
            </td>
            <td>
              <a
                href="#"
                class="link-primary text-decoration-underline"
                @click.prevent="selected = order"
              >
                View
              </a>
            </td>
            <td>{{ order.created_at }}</td>
          </tr>
        </tbody>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import { sampleOrders } from '../staticData'

const orders = ref(sampleOrders)
const selected = ref(null)

const tableOptions = {
  pageLength: 10,
  order: [[4, 'desc']],
  columnDefs: [
    { orderable: false, targets: 3 },
    { className: 'text-start', targets: '_all' },
  ],
}

function statusClass(status) {
  if (status === 'paid') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-secondary'
}
</script>
