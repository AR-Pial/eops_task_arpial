<template>
  <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1100">
    <div
      v-for="t in toasts"
      :id="`toast-${t.id}`"
      :key="t.id"
      class="toast align-items-center border-0"
      :class="`text-bg-${t.variant}`"
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div class="d-flex">
        <div class="toast-body">{{ t.message }}</div>
        <button
          type="button"
          class="btn-close btn-close-white me-2 m-auto"
          data-bs-dismiss="toast"
          aria-label="Close"
        ></button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, watch } from 'vue'
import { Toast } from 'bootstrap'
import { removeToast, toasts } from '../toast'

watch(
  () => toasts.value.map((t) => t.id),
  async (ids, prevIds = []) => {
    await nextTick()
    for (const id of ids) {
      if (prevIds.includes(id)) continue
      const item = toasts.value.find((t) => t.id === id)
      const el = document.getElementById(`toast-${id}`)
      if (!item || !el) continue

      const instance = Toast.getOrCreateInstance(el, {
        animation: true,
        autohide: true,
        delay: item.delay,
      })
      el.addEventListener('hidden.bs.toast', () => removeToast(id), { once: true })
      instance.show()
    }
  },
)
</script>
