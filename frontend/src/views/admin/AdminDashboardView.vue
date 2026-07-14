<template>
  <AdminLayout>
    <h2 class="h4 mb-3">Dashboard</h2>
    <div class="row g-3">
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Products</div>
            <div class="fs-4 fw-semibold">6</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Orders</div>
            <div class="fs-4 fw-semibold">3</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Payments</div>
            <div class="fs-4 fw-semibold">3</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="text-muted small">Revenue</div>
            <div class="fs-4 fw-semibold">$129.49</div>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import AdminLayout from '../../layouts/AdminLayout.vue'
</script>
