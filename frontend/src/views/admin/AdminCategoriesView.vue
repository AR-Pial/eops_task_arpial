<template>
  <AdminLayout>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Categories</h2>
      <button type="button" class="btn btn-primary" @click="openCreate">Add category</button>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <p v-if="loading" class="text-muted mb-0">Loading...</p>
        <table v-else class="table table-striped align-middle mb-0">
          <thead>
            <tr>
              <th>Serial</th>
              <th>Name</th>
              <th>Parent</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(cat, index) in categories" :key="cat.id">
              <td>{{ index + 1 }}</td>
              <td>{{ cat.name }}</td>
              <td>{{ parentName(cat.parent) || '—' }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="openEdit(cat)">
                  Edit
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="onDelete(cat)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="showModal"
      class="modal fade show d-block"
      tabindex="-1"
      style="background: rgba(0, 0, 0, 0.45)"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <form @submit.prevent="onSave">
            <div class="modal-header">
              <h5 class="modal-title">{{ editingId ? 'Edit category' : 'Add category' }}</h5>
              <button type="button" class="btn-close" @click="closeModal"></button>
            </div>
            <div class="modal-body">
              <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
              <div class="mb-3">
                <label class="form-label" for="cat-name">Name</label>
                <input id="cat-name" v-model="form.name" class="form-control" required />
              </div>
              <div class="mb-0">
                <label class="form-label" for="cat-parent">Parent</label>
                <select id="cat-parent" v-model="form.parent" class="form-select">
                  <option value="">None (root)</option>
                  <option
                    v-for="cat in parentOptions"
                    :key="cat.id"
                    :value="cat.id"
                  >
                    {{ cat.name }}
                  </option>
                </select>
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
import { computed, onMounted, reactive, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import $axios from '../../axios'
import API from '../../apiUrls'

const categories = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const formError = ref('')
const showModal = ref(false)
const editingId = ref(null)

const form = reactive({
  name: '',
  parent: '',
})

const parentOptions = computed(() =>
  categories.value.filter((c) => c.id !== editingId.value),
)

function parentName(parentId) {
  if (!parentId) return ''
  return categories.value.find((c) => c.id === parentId)?.name || ''
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

function resetForm() {
  form.name = ''
  form.parent = ''
  formError.value = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  showModal.value = true
}

function openEdit(cat) {
  editingId.value = cat.id
  form.name = cat.name
  form.parent = cat.parent || ''
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
}

async function loadCategories() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await $axios.get(API.categories)
    categories.value = Array.isArray(data) ? data : data.results || []
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
    parent: form.parent || null,
  }
  try {
    if (editingId.value) {
      await $axios.put(API.categoryDetail(editingId.value), payload)
      success.value = 'Category updated.'
    } else {
      await $axios.post(API.categories, payload)
      success.value = 'Category created.'
    }
    closeModal()
    await loadCategories()
  } catch (err) {
    formError.value = parseApiError(err)
  } finally {
    saving.value = false
  }
}

async function onDelete(cat) {
  if (!window.confirm(`Delete category "${cat.name}"?`)) return
  error.value = ''
  success.value = ''
  try {
    await $axios.delete(API.categoryDetail(cat.id))
    success.value = 'Category deleted.'
    await loadCategories()
  } catch (err) {
    error.value = parseApiError(err)
  }
}

onMounted(loadCategories)
</script>
