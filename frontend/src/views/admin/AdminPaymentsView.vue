<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Payments</h2>
    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <DataTable class="table table-striped table-hover align-middle w-100" :options="tableOptions">
          <thead>
            <tr>
              <th>ID</th>
              <th>Order</th>
              <th>Provider</th>
              <th>Transaction</th>
              <th>Status</th>
              <th>Details</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td>
              <td>#101</td>
              <td>STRIPE</td>
              <td><code class="small">pi_3MxTestAbc123</code></td>
              <td><span class="badge text-bg-success">success</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/payments/1">View</router-link></td>
              <td>2026-07-10 14:25</td>
            </tr>
            <tr>
              <td>2</td>
              <td>#102</td>
              <td>BKASH</td>
              <td><code class="small">TRX987654321</code></td>
              <td><span class="badge text-bg-warning">pending</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/payments/2">View</router-link></td>
              <td>2026-07-12 09:06</td>
            </tr>
            <tr>
              <td>3</td>
              <td>#103</td>
              <td>STRIPE</td>
              <td><code class="small">pi_3MxFailXyz789</code></td>
              <td><span class="badge text-bg-danger">failed</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/payments/3">View</router-link></td>
              <td>2026-07-08 18:41</td>
            </tr>
          </tbody>
        </DataTable>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import AdminLayout from '../../layouts/AdminLayout.vue'

const tableOptions = {
  pageLength: 10,
  order: [[6, 'desc']],
  columnDefs: [
    { orderable: false, targets: 5 },
    { className: 'text-start', targets: '_all' },
  ],
}
</script>
