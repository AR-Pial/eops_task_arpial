import { ref } from 'vue'

let nextId = 0

export const toasts = ref([])

export function showToast(message, { variant = 'success', delay = 3000 } = {}) {
  toasts.value.push({
    id: ++nextId,
    message,
    variant,
    delay,
  })
}

export function removeToast(id) {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}
