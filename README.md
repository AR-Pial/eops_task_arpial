# EOPS — E-commerce Ordering & Payment System

## Stack

- **Backend:** Django 6 + Django REST Framework, PostgreSQL, Redis
- **Frontend:** Vue 3 + Vite
- **Payments:** Strategy pattern (`StripeStrategy`, `BkashStrategy`)

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional but required for category-tree caching; the API falls back to DB if Redis is down)

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DB_* (and Stripe test keys if you want real Elements).
# bKash sandbox credentials are already filled in .env.example.
```

### PostgreSQL

Create a database matching `DB_NAME` in `.env`:

```sql
CREATE DATABASE eops;
```

### Redis

Start Redis locally (default URL in `.env.example`):

```bash
redis-server
# or: docker run -d -p 6379:6379 redis:7
```

Leave `REDIS_URL` as-is, or point it at your instance. Category hierarchy DFS uses Redis to cache the tree; without Redis, trees are rebuilt from PostgreSQL each time.

### Migrate & run

```bash
python manage.py migrate
python manage.py seed_demo          # admin user + sample categories/products
python manage.py runserver
```

`seed_demo` creates `admin@eops.local` / `admin123` (superadmin) and a catalog of categories + products. Re-runs are safe (upsert by email/SKU). Use `--clear` to wipe categories/products first, or `--email` / `--password` to override admin credentials.

API base: `http://127.0.0.1:8000`

## Frontend setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Storefront: `http://127.0.0.1:5173`

Set `VITE_API_BASE_URL` to the backend URL. For Stripe Elements, set `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_test_…`) in `frontend/.env`. Leave payment secrets empty only if you want mock flows (see below).

## Environment variables (backend)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret |
| `DEBUG` / `ALLOWED_HOSTS` | Dev settings |
| `DB_*` | PostgreSQL connection |
| `REDIS_URL` | Category tree cache |
| `STRIPE_SECRET_KEY` | Stripe PaymentIntents (empty → mock) |
| `STRIPE_WEBHOOK_SECRET` | Verifies Stripe webhook signatures (`whsec_…`) |
| `BKASH_*` | bKash tokenized checkout (empty → mock) |
| `BKASH_WEBHOOK_SECRET` | Optional HMAC for `X-Bkash-Signature` (status still verified via Query API) |

API secrets stay in `.env` (gitignored). `.env.example` already includes official **bKash sandbox** credentials so reviewers can test the real sandbox UI without requesting merchant access. Put your own Stripe **test** keys in `.env` only — never commit real secrets.

## Quick test guide (reviewers)

With both servers running:

1. Open `http://127.0.0.1:5173`
2. Register a customer (or log in)
3. Browse products → add to cart → Checkout
4. Pay with **Stripe** or **bKash** as below
5. Check **My orders** / **My payments** after payment

### Admin

```bash
python manage.py seed_demo
# or: python manage.py createsuperuser
```

Default seeded login: `admin@eops.local` / `admin123`. Open `/admin` routes in the storefront (or Django admin at `http://127.0.0.1:8000/admin/`) to manage products, orders, and payments. User type must be `admin` / `superadmin` for the Vue admin pages.

### bKash sandbox (recommended)

`.env.example` ships with public bKash sandbox app credentials. After `cp .env.example .env`, choose **bKash** at checkout — the app redirects to the real bKash sandbox payment page (`bkashURL`).

**Sandbox wallet (enter on the bKash page):**

| Field | Value |
|-------|--------|
| Number | `01770618575` (or `01929918378`) |
| OTP | `123456` |
| PIN | `12121` |

Flow:

1. Place order → provider **bKash**
2. Browser opens bKash sandbox UI
3. Enter wallet / OTP / PIN above
4. bKash redirects back to `/checkout?paymentID=…&status=success|failure|cancel`
5. App confirms payment automatically; order becomes `paid` on success

Cancel or fail on the sandbox page to exercise failed/canceled order handling and pay-again.

### Stripe

| Mode | Setup |
|------|--------|
| **Mock** | Leave `STRIPE_SECRET_KEY` empty → checkout shows **Confirm payment** (no card form) |
| **Test (real Elements)** | Set `STRIPE_SECRET_KEY=sk_test_…` and `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_…` |

**Test cards** (use in Stripe Elements; any future expiry, any CVC, any postal code):

| Scenario | Card number |
|----------|-------------|
| Success | `4242 4242 4242 4242` |
| Decline | `4000 0000 0000 0002` |
| Insufficient funds | `4000 0000 0000 9995` |
| Requires 3D Secure | `4000 0025 0000 3155` |

Optional webhooks:

```bash
stripe listen --forward-to localhost:8000/api/payments/webhooks/stripe/
```

Put the printed `whsec_…` into `STRIPE_WEBHOOK_SECRET`. Requests without a valid `Stripe-Signature` are rejected when the secret is set.

bKash webhooks (`POST /api/payments/webhooks/bkash/`) only take `paymentID` from the body; **status is always re-checked** via bKash Query Payment API (so a forged `transactionStatus: Completed` alone cannot mark an order paid). Optionally set `BKASH_WEBHOOK_SECRET` and send `X-Bkash-Signature: sha256=<hmac-hex>` over the raw body.

### Orders & stock

1. Create an order with line items → status `pending`
2. Complete payment → order `paid`, stock reduced (row-locked)
3. Cancel a pending order → `canceled`; reopen / pay again from checkout when allowed

### Categories & Redis

- `GET /api/categories/tree/` uses DFS + Redis cache when `REDIS_URL` is up
- With Redis stopped, the API still works (rebuilds from PostgreSQL)

## API overview

Auth uses DRF **TokenAuthentication**. After register/login, send `Authorization: Token <key>`.

| Area | Endpoints |
|------|-----------|
| Auth | `POST /api/auth/register/`, `POST /api/auth/login/`, `GET\|PATCH /api/auth/me/` |
| Categories | `GET /api/categories/`, `GET /api/categories/tree/`, admin CRUD |
| Products | `GET /api/products/`, `GET /api/products/{id}/`, `GET /api/products/{id}/related/`, admin CRUD |
| Orders | `GET\|POST /api/orders/`, `GET /api/orders/{id}/`, `POST …/cancel/`, `POST …/reopen/` |
| Payments | `GET /api/payments/`, `POST /api/payments/checkout/`, `POST /api/payments/confirm/` |
| Webhooks | `POST /api/payments/webhooks/stripe/`, `POST /api/payments/webhooks/bkash/` |

**Checkout body:** `{ "order_id": "<uuid>", "provider": "stripe" | "bkash" }`  
**Confirm body:** `{ "payment_id": "<uuid>" }` or `{ "transaction_id": "<paymentID>", "callback_status": "success\|failure\|cancel" }`

## Architecture notes (assessment)

- **OOP:** `User`, `Product`, `Order` / `OrderItem`, `Payment` domain models
- **Data:** Relational tables with indexes on FK/status/SKU/email; `Category` self-FK hierarchy
- **Algorithms:** Deterministic order item subtotals and order totals; stock reduction with `SELECT FOR UPDATE`
- **Strategy pattern:** `PaymentStrategy` + factory — add providers without changing order core
- **DFS + cache:** Category tree DFS for filters/related products; tree cached in Redis
