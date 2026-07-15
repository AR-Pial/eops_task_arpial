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
# Edit .env: set DB_*, optional Redis, Stripe, and bKash credentials
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
python manage.py createsuperuser   # optional; use admin email + password
python manage.py runserver
```

API base: `http://127.0.0.1:8000`

## Frontend setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Storefront: `http://127.0.0.1:5173`

Set `VITE_API_BASE_URL` to the backend URL. For live Stripe Elements, set `VITE_STRIPE_PUBLISHABLE_KEY`. With empty payment keys, the backend uses mock Stripe/bKash flows suitable for local demos.

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

API keys stay in `.env` (gitignored), not in source.

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
**Confirm body:** `{ "payment_id": "<uuid>", "callback_status": "…" }` (optional status for cancel/fail)

### Typical order flow

1. Customer creates an order with line items → status `pending`
2. Checkout with a provider → payment row + provider session
3. Confirm or webhook → payment `success` / `failed`
4. On success → order `paid` and product stock reduced safely under row locks

## Architecture notes (assessment)

- **OOP:** `User`, `Product`, `Order` / `OrderItem`, `Payment` domain models
- **Data:** Relational tables with indexes on FK/status/SKU/email; `Category` self-FK hierarchy
- **Algorithms:** Deterministic order item subtotals and order totals; stock reduction with `SELECT FOR UPDATE`
- **Strategy pattern:** `PaymentStrategy` + factory — add providers without changing order core
- **DFS + cache:** Category tree DFS for filters/related products; tree cached in Redis

## Stripe webhooks (optional)

```bash
stripe listen --forward-to localhost:8000/api/payments/webhooks/stripe/
```

Put the printed `whsec_…` into `STRIPE_WEBHOOK_SECRET`. Requests without a valid `Stripe-Signature` are rejected when the secret is set.
