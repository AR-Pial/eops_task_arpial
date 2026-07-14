const CART_KEY = 'cart'

export function getCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) || '[]')
  } catch {
    return []
  }
}

export function saveCart(items) {
  localStorage.setItem(CART_KEY, JSON.stringify(items))
}

export function addToCart(product) {
  const cart = getCart()
  const row = cart.find((item) => item.product_id === product.id)

  if (row) {
    row.quantity += 1
  } else {
    cart.push({
      product_id: product.id,
      name: product.name,
      price: product.price,
      quantity: 1,
    })
  }

  saveCart(cart)
  return cart
}

export function updateQty(productId, quantity) {
  let cart = getCart()

  if (quantity < 1) {
    cart = cart.filter((item) => item.product_id !== productId)
  } else {
    const row = cart.find((item) => item.product_id === productId)
    if (row) row.quantity = quantity
  }

  saveCart(cart)
  return cart
}

export function removeFromCart(productId) {
  const cart = getCart().filter((item) => item.product_id !== productId)
  saveCart(cart)
  return cart
}

export function clearCart() {
  localStorage.removeItem(CART_KEY)
}

export function cartTotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0)
}
