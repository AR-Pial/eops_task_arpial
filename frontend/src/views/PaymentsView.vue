<template>
  <div>
    <Navbar />

    <div class="container">
      <h2>Payments</h2>

      <DataTable class="table table-striped table-hover align-middle w-100" :options="tableOptions">
        <thead>
          <tr>
            <th>ID</th>
            <th>Order</th>
            <th>Provider</th>
            <th>Transaction ID</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in payments" :key="payment.id">
            <td>{{ payment.id }}</td>
            <td>#{{ payment.order_id }}</td>
            <td class="text-uppercase">{{ payment.provider }}</td>
            <td><code class="small">{{ payment.transaction_id }}</code></td>
            <td>
              <span class="badge" :class="statusClass(payment.status)">{{ payment.status }}</span>
            </td>
            <td>{{ payment.created_at }}</td>
          </tr>
        </tbody>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import { samplePayments } from '../staticData'

const payments = ref(samplePayments)

const tableOptions = {
  pageLength: 10,
  order: [[5, 'desc']],
  columnDefs: [{ className: 'text-start', targets: '_all' }],
}

function statusClass(status) {
  if (status === 'success') return 'text-bg-success'
  if (status === 'pending') return 'text-bg-warning'
  return 'text-bg-danger'
}
</script>
