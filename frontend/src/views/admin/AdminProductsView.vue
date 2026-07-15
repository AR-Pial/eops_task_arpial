<template>
  <AdminLayout>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Products</h2>
      <button type="button" class="btn btn-primary" @click="openCreate">
        Add product
      </button>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <p v-if="loading" class="text-muted mb-0">Loading products...</p>
        <DataTable
          v-else
          :key="tableKey"
          class="table table-striped table-hover align-middle w-100"
          :options="tableOptions"
        >
          <thead>
            <tr>
              <th>Serial</th>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Featured</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in products" :key="product.id">
              <td></td>
              <td>{{ product.sku }}</td>
              <td>{{ product.name }}</td>
              <td>{{ product.category_name || '—' }}</td>
              <td>{{ formatBDT(product.price) }}</td>
              <td>{{ product.stock }}</td>
              <td>
                <span
                  class="badge"
                  :class="product.is_featured ? 'text-bg-warning' : 'text-bg-light'"
                >
                  {{ product.is_featured ? 'yes' : 'no' }}
                </span>
              </td>
              <td>
                <span
                  class="badge"
                  :class="product.status === 'active' ? 'text-bg-success' : 'text-bg-secondary'"
                >
                  {{ product.status }}
                </span>
              </td>
              <td>{{ formatDate(product.created_at) }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="openEdit(product)">
                  Edit
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="onDelete(product)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </DataTable>
      </div>
    </div>

    <div
      v-if="showModal"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      style="background: rgba(0, 0, 0, 0.45)"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="onSave">
            <div class="modal-header">
              <h5 class="modal-title">{{ editingId ? 'Edit product' : 'Add product' }}</h5>
              <button type="button" class="btn-close" @click="closeModal"></button>
            </div>
            <div class="modal-body">
              <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>

              <div class="mb-3">
                <label class="form-label" for="name">Name</label>
                <input id="name" v-model="form.name" type="text" class="form-control" required />
              </div>

              <div class="mb-3">
                <label class="form-label" for="sku">SKU</label>
                <input id="sku" v-model="form.sku" type="text" class="form-control" required />
              </div>

              <div class="mb-3">
                <label class="form-label" for="description">Description</label>
                <textarea id="description" v-model="form.description" class="form-control" rows="3"></textarea>
              </div>

              <div class="mb-3">
                <label class="form-label" for="category">Category</label>
                <select id="category" v-model="form.category" class="form-select">
                  <option value="">None</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </select>
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label" for="price">Price (৳)</label>
                  <input
                    id="price"
                    v-model.number="form.price"
                    type="number"
                    class="form-control"
                    min="0"
                    step="0.01"
                    required
                  />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label" for="stock">Stock</label>
                  <input
                    id="stock"
                    v-model.number="form.stock"
                    type="number"
                    class="form-control"
                    min="0"
                    step="1"
                    required
                  />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label" for="status">Status</label>
                <select id="status" v-model="form.status" class="form-select">
                  <option value="active">active</option>
                  <option value="inactive">inactive</option>
                </select>
              </div>

              <div class="form-check">
                <input
                  id="is_featured"
                  v-model="form.is_featured"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label" for="is_featured">
                  Featured
                </label>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import $axios from '../../axios'
import API from '../../apiUrls'
import { formatBDT } from '../../utils/money'
import { serialColumnDrawCallback } from '../../utils/dataTableSerial'

const products = ref([])
const categories = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const formError = ref('')
const showModal = ref(false)
const editingId = ref(null)
const tableKey = ref(0)

const form = reactive({
  name: '',
  sku: '',
  description: '',
  category: '',
  price: 0,
  stock: 0,
  status: 'active',
  is_featured: false,
})

const tableOptions = {
  pageLength: 10,
  order: [[8, 'desc']],
  columnDefs: [
    { orderable: false, searchable: false, targets: 0 },
    { orderable: false, targets: 9 },
    { className: 'text-start', targets: '_all' },
  ],
  drawCallback: serialColumnDrawCallback(),
}

function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  return d.toLocaleString()
}

function resetForm() {
  form.name = ''
  form.sku = ''
  form.description = ''
  form.category = ''
  form.price = 0
  form.stock = 0
  form.status = 'active'
  form.is_featured = false
  formError.value = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(product) {
  editingId.value = product.id
  form.name = product.name
  form.sku = product.sku
  form.description = product.description || ''
  form.category = product.category || ''
  form.price = Number(product.price)
  form.stock = product.stock
  form.status = product.status
  form.is_featured = Boolean(product.is_featured)
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
  formError.value = ''
}

function parseApiError(err) {
  const data = err.response?.data
  if (!data) return 'Request failed'
  if (typeof data.detail === 'string') return data.detail
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return 'Request failed'
}

async function loadCategories() {
  const { data } = await $axios.get(API.categories)
  categories.value = Array.isArray(data) ? data : data.results || []
}

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await $axios.get(API.products)
    products.value = Array.isArray(data) ? data : data.results || []
    tableKey.value += 1
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    loading.value = false
  }
}

async function onSave() {
  saving.value = true
  formError.value = ''
  success.value = ''

  const payload = {
    name: form.name.trim(),
    sku: form.sku.trim(),
    description: form.description,
    category: form.category || null,
    price: form.price,
    stock: form.stock,
    status: form.status,
    is_featured: form.is_featured,
  }

  try {
    if (editingId.value) {
      await $axios.put(API.productDetail(editingId.value), payload)
      success.value = 'Product updated.'
    } else {
      await $axios.post(API.products, payload)
      success.value = 'Product created.'
    }
    closeModal()
    await loadProducts()
  } catch (err) {
    formError.value = parseApiError(err)
  } finally {
    saving.value = false
  }
}

async function onDelete(product) {
  if (!window.confirm(`Delete "${product.name}"?`)) return
  error.value = ''
  success.value = ''
  try {
    await $axios.delete(API.productDetail(product.id))
    success.value = 'Product deleted.'
    await loadProducts()
  } catch (err) {
    error.value = parseApiError(err)
  }
}

onMounted(async () => {
  try {
    await loadCategories()
  } catch {
    categories.value = []
  }
  await loadProducts()
})
</script>
