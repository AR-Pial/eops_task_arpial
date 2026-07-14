<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Products</h2>
    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <DataTable class="table table-striped table-hover align-middle w-100" :options="tableOptions">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>WH-100</td>
              <td>Wireless Headphones</td>
              <td>$89.99</td>
              <td>24</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-01 10:00</td>
            </tr>
            <tr>
              <td>HUB-01</td>
              <td>USB-C Hub</td>
              <td>$39.50</td>
              <td>50</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-02 11:15</td>
            </tr>
            <tr>
              <td>KB-75</td>
              <td>Mechanical Keyboard</td>
              <td>$119.00</td>
              <td>12</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-03 09:30</td>
            </tr>
            <tr>
              <td>LAMP-2</td>
              <td>Desk Lamp</td>
              <td>$45.00</td>
              <td>0</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-04 14:00</td>
            </tr>
            <tr>
              <td>ST-17</td>
              <td>Laptop Stand</td>
              <td>$54.99</td>
              <td>33</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-05 16:20</td>
            </tr>
            <tr>
              <td>CAM-HD</td>
              <td>Webcam HD</td>
              <td>$69.00</td>
              <td>18</td>
              <td><span class="badge text-bg-success">active</span></td>
              <td>2026-07-06 08:45</td>
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
  order: [[5, 'desc']],
  columnDefs: [{ className: 'text-start', targets: '_all' }],
}
</script>
