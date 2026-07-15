import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import CheckoutView from '../views/CheckoutView.vue'
import OrdersView from '../views/OrdersView.vue'
import PaymentsView from '../views/PaymentsView.vue'
import ProfileView from '../views/ProfileView.vue'
import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import AdminProductsView from '../views/admin/AdminProductsView.vue'
import AdminCategoriesView from '../views/admin/AdminCategoriesView.vue'
import AdminOrdersView from '../views/admin/AdminOrdersView.vue'
import AdminOrderDetailView from '../views/admin/AdminOrderDetailView.vue'
import AdminPaymentsView from '../views/admin/AdminPaymentsView.vue'
import AdminPaymentDetailView from '../views/admin/AdminPaymentDetailView.vue'
import NotFoundView from '../views/NotFoundView.vue'
import PaymentConfirmationView from '../views/PaymentConfirmationView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/products/:id',
    name: 'product-detail',
    component: ProductDetailView,
  },
  {
    path: '/checkout',
    name: 'checkout',
    component: CheckoutView,
  },
  {
    path: '/confirmation',
    name: 'payment-confirmation',
    component: PaymentConfirmationView,
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'orders',
    component: OrdersView,
    meta: { requiresAuth: true },
  },
  {
    path: '/payments',
    name: 'payments',
    component: PaymentsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guest: true },
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: AdminDashboardView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/products',
    name: 'admin-products',
    component: AdminProductsView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/categories',
    name: 'admin-categories',
    component: AdminCategoriesView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/orders',
    name: 'admin-orders',
    component: AdminOrdersView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/orders/:id',
    name: 'admin-order-detail',
    component: AdminOrderDetailView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/payments',
    name: 'admin-payments',
    component: AdminPaymentsView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/payments/:id',
    name: 'admin-payment-detail',
    component: AdminPaymentDetailView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
  },
]

const ADMIN_TYPES = new Set(['admin', 'superadmin'])

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

function isAdminUser(user) {
  return !!user && ADMIN_TYPES.has(user.user_type)
}

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const user = getStoredUser()

  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { next: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !isAdminUser(user)) {
    return { name: 'home' }
  }

  if (to.meta.guest && token) {
    if (isAdminUser(user)) {
      return { name: 'admin-dashboard' }
    }
    return { name: 'home' }
  }

  return true
})

export default router
