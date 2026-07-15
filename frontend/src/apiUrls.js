const API = {
  register: '/api/auth/register/',
  login: '/api/auth/login/',
  me: '/api/auth/me/',
  categories: '/api/categories/',
  categoryDetail: (id) => `/api/categories/${id}/`,
  products: '/api/products/',
  productDetail: (id) => `/api/products/${id}/`,
  productRelated: (id) => `/api/products/${id}/related/`,
  orders: '/api/orders/',
  orderDetail: (id) => `/api/orders/${id}/`,
  orderCancel: (id) => `/api/orders/${id}/cancel/`,
  orderReopen: (id) => `/api/orders/${id}/reopen/`,
  payments: '/api/payments/',
  paymentDetail: (id) => `/api/payments/${id}/`,
  checkout: '/api/payments/checkout/',
  confirmPayment: '/api/payments/confirm/',
}

export default API
