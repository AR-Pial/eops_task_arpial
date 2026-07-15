# EOPS Project Report

**E-commerce Ordering & Payment System**  
**Candidate deliverable for Raco AI — Backend Engineer technical assessment**

Use this document as the Project Report (copy into a Google Doc and share a viewable link for the submission form).

| Artifact | Location |
|----------|----------|
| Source repository | GitHub public repo (this project) |
| Architecture / ERD / payment diagrams | `docs/4.1-documentation.md` |
| Postman collection | `docs/EOPS.postman_collection.json` |
| Env + ngrok guide | `docs/environment-and-ngrok.md` |
| README (run / Docker / seed) | `README.md` |

---

## 1. Implementation approach and rationale

### 1.1 Stack choice

| Layer | Choice | Rationale |
|-------|--------|-----------|
| API | Django 6 + Django REST Framework | Mature ORM/migrations, permission model, strong fit for relational ecommerce schema |
| DB | PostgreSQL | ACID, row locking (`SELECT FOR UPDATE`) for safe stock updates |
| Cache | Redis | Category-tree cache per DFS requirement; DB fallback if Redis is down |
| Payments | Strategy pattern (Stripe + bKash) | Switch providers without changing order orchestration |
| Frontend | Vue 3 + Vite | Storefront + admin to exercise the full order/payment flow (beyond pure API) |
| Deploy | Docker Compose (`web` + `db` + `redis`) | One-command reviewer path with migrations + seed |

### 1.2 Domain / OOP design

Business entities are modeled as classes with behavior, not anemic tables:

- **User** — registration, auth identity, typed roles (`customer` / `admin` / `superadmin`)
- **Product** / **Category** — catalog; `Product.reduce_stock()` with locking
- **Order** / **OrderItem** — totals (`calculate_total`), lifecycle (`mark_paid`, cancel/reopen)
- **Payment** — provider-agnostic record (`provider`, `transaction_id`, `amount` snapshot, `status`, `raw_response`)

`PaymentService` orchestrates checkout → confirm → webhook and delegates provider specifics to strategies.

### 1.3 Strategy pattern (payments)

```text
PaymentService
    └── PaymentStrategyFactory.get(provider)
            ├── StripeStrategy  (PaymentIntent create / confirm / webhook)
            └── BkashStrategy   (create / execute / query / webhook)
```

Abstract base: `PaymentStrategy` (`initiate_payment`, `confirm_payment`, `handle_webhook`).  
New providers register via `PaymentStrategyFactory.register` without editing order or checkout views.

### 1.4 Relational schema & efficiency

Tables: Users, Categories (self-FK tree), Products, Orders, OrderItems, Payments.  
Indexes on common filters (email, SKU, status, FKs, `transaction_id`).  
`Payment.amount` is stored at checkout as a snapshot (not only derived from the order at read time).

### 1.5 Algorithms

- **Totals:** `subtotal = price × quantity` (quantize to 2 dp); order total = sum of line subtotals.
- **Stock:** on successful payment, lock order items’ products (`select_for_update`) and reduce stock atomically; fail closed if insufficient stock.
- **DFS + cache:** build adjacency list for categories once; `dfs_collect_descendant_ids` walks children for include-descendants filters and related-product recommendations; tree JSON cached in Redis with invalidation on category CUD.

### 1.6 Security posture (assessment scope)

- Secrets via environment variables (`.env` gitignored; `.env.example` for reviewers).
- Stripe webhook signature verification when `STRIPE_WEBHOOK_SECRET` is set.
- bKash webhook: optional HMAC; **payment status always re-queried** from bKash (payload not trusted alone).
- Token authentication for customer/admin APIs; ownership checks on orders/payments.

---

## 2. Testing approach and reports

### 2.1 Approach

| Layer | Coverage |
|-------|----------|
| Model / unit | User, Product (stock), Order (totals, pay/cancel), Payment uniqueness & amount |
| API | Auth register/login, product/order CRUD paths, checkout/confirm per provider (mock) |
| Webhooks | Stripe signature accept/reject; bKash query re-verification + optional HMAC |
| Isolation | `@override_settings` empties live keys so CI/local tests use mocks |

Run:

```bash
# Docker
docker compose run --rm web python manage.py test apps

# Local
cd backend && python manage.py test apps
```

### 2.2 Latest test report

| Metric | Result |
|--------|--------|
| Command | `python manage.py test apps` (via Docker Compose `web`) |
| Tests run | **68** |
| Failures / errors | **0** |
| Result | **OK** |

Suites include:

- `apps.accounts.tests` — auth / user model  
- `apps.products.tests` — models / stock  
- `apps.orders.tests` — order model + API  
- `apps.payments.tests` — models, checkout/confirm API, Stripe & bKash webhooks  

### 2.3 Manual verification path (reviewers)

1. `docker compose up --build`  
2. `cd frontend && npm install && npm run dev`  
3. Customer purchase with **bKash sandbox** or **Stripe mock/test**  
4. Admin: `admin@eops.local` / `admin123`  

Details: `README.md` → “5-minute reviewer path” and “Quick test guide”.

---

## 3. API and router documentation

### 3.1 Router map

Root: `backend/config/urls.py`

| Prefix | Module | Notes |
|--------|--------|-------|
| `/api/schema/` `/api/docs/` `/api/redoc/` | drf-spectacular | OpenAPI / Swagger / ReDoc |
| `/api/auth/` | `apps.accounts.urls` | `register/`, `login/`, `me/` |
| `/api/categories/` | `CategoryViewSet` router | list/tree + admin CRUD |
| `/api/products/` | `ProductViewSet` router | list/detail/related + admin CRUD |
| `/api/orders/` | `OrderViewSet` router | create/list/detail, `cancel/`, `reopen/` |
| `/api/payments/` | payments urls | ViewSet list/detail + `checkout/`, `confirm/`, webhooks |

Auth: `Authorization: Token <key>` after register/login.

### 3.2 Payment routes

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/api/payments/` | Token |
| `GET` | `/api/payments/{id}/` | Token |
| `POST` | `/api/payments/checkout/` | Token — `{ order_id, provider }` |
| `POST` | `/api/payments/confirm/` | Token — `{ payment_id }` or `{ transaction_id, callback_status? }` |
| `POST` | `/api/payments/webhooks/stripe/` | Public (signature when secret set) |
| `POST` | `/api/payments/webhooks/bkash/` | Public (HMAC optional; Query API mandatory) |

Full tables, ERD, and sequence diagrams: `docs/4.1-documentation.md`.  
Postman: `docs/EOPS.postman_collection.json`.

### 3.3 Diagrams (summary)

Included in `docs/4.1-documentation.md` (Mermaid):

1. System architecture (Vue → DRF → Strategy → Stripe/bKash; Postgres + Redis)  
2. ERD (Users, Categories, Products, Orders, OrderItems, Payments)  
3. Stripe PaymentIntent + webhook flow  
4. bKash create / execute / query flow  
5. Order/payment state transitions  

---

## 4. Local environment & ngrok (submission field)

Full guide: **`docs/environment-and-ngrok.md`**.

Summary:

1. Copy `.env.example` → `.env` for backend and frontend.  
2. Run API on port `8000` (Compose or `runserver`).  
3. `ngrok http 8000` → HTTPS URL.  
4. Add ngrok hostname to `ALLOWED_HOSTS`.  
5. Point Stripe (and optionally bKash) webhook URLs at  
   `https://<ngrok-host>/api/payments/webhooks/...`  
6. Set `STRIPE_WEBHOOK_SECRET` from Dashboard or Stripe CLI.

---

## 5. Final verdict

The system meets the assessment’s functional and design requirements:

- User, product, order, and multi-provider payment APIs with migrations and validation  
- OOP domain models and deterministic total/stock algorithms  
- **Strategy pattern** for Stripe and bKash with webhook handling  
- **DFS + Redis** category hierarchy for filtering/recommendations  
- Documentation (architecture, ERD, API, payment flows), Postman, seed data, Docker Compose, and automated tests (**68 passed**)  
- Local webhook exposure documented via **ngrok** (plus Stripe CLI alternative)

**Verdict: Ready for submission and reviewer evaluation.** Remaining optional polish (e.g. Vercel frontend hosting) is outside the core Backend Engineer evaluation focus stated in the invite (OOP, Strategy, DFS + caching, secure payment integration).

---

*End of report.*
