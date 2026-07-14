<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Orders</h2>
    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <DataTable class="table table-striped table-hover align-middle w-100" :options="tableOptions">
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
            <tr>
              <td>#101</td>
              <td>$129.49</td>
              <td><span class="badge text-bg-success">paid</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/orders/101">View</router-link></td>
              <td>2026-07-10 14:22</td>
            </tr>
            <tr>
              <td>#102</td>
              <td>$119.00</td>
              <td><span class="badge text-bg-warning">pending</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/orders/102">View</router-link></td>
              <td>2026-07-12 09:05</td>
            </tr>
            <tr>
              <td>#103</td>
              <td>$69.00</td>
              <td><span class="badge text-bg-secondary">canceled</span></td>
              <td><router-link class="link-primary text-decoration-underline" to="/admin/orders/103">View</router-link></td>
              <td>2026-07-08 18:40</td>
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
  order: [[4, 'desc']],
  columnDefs: [
    { orderable: false, targets: 3 },
    { className: 'text-start', targets: '_all' },
  ],
}
</script>
