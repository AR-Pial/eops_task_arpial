const API = {
  register: '/api/auth/register/',
  login: '/api/auth/login/',
  me: '/api/auth/me/',
  products: '/api/products/',
  productDetail: (id) => `/api/products/${id}/`,
  orders: '/api/orders/',
  orderDetail: (id) => `/api/orders/${id}/`,
  checkout: '/api/payments/checkout/',
}

export default API
