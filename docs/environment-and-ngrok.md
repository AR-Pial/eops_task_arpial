# Environment configuration & local ngrok setup

This guide covers local environment variables and how to expose the backend with **ngrok** so Stripe / bKash can reach webhook endpoints running on your machine.

Related files:

- Backend template: [`backend/.env.example`](../backend/.env.example)
- Frontend template: [`frontend/.env.example`](../frontend/.env.example)
- Quick start: [`README.md`](../README.md)

---

## 1. Environment configuration

### 1.1 Backend (`backend/.env`)

```bash
cd backend
cp .env.example .env
# edit values as needed
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | Yes | Django secret |
| `DEBUG` | Dev | `True` locally |
| `ALLOWED_HOSTS` | Yes | Hosts Django accepts (include your ngrok hostname when tunneling) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Yes | PostgreSQL |
| `REDIS_URL` | Recommended | Category tree DFS cache (`redis://127.0.0.1:6379/0`) |
| `STRIPE_SECRET_KEY` | Optional | Empty → mock Stripe; `sk_test_…` → real test mode |
| `STRIPE_WEBHOOK_SECRET` | For signed webhooks | `whsec_…` from Stripe CLI or Dashboard |
| `BKASH_APP_KEY` / `BKASH_APP_SECRET` / `BKASH_USERNAME` / `BKASH_PASSWORD` | Optional | Empty → mock; `.env.example` ships sandbox values |
| `BKASH_BASE_URL` | Sandbox/live | Sandbox URL by default; swap for live URL when going live |
| `BKASH_CALLBACK_URL` | Checkout return | Frontend return URL (default `http://localhost:5173/checkout`) |
| `BKASH_WEBHOOK_SECRET` | Optional | HMAC for `X-Bkash-Signature` on webhook POSTs |

**Docker Compose:** `DB_HOST` / `REDIS_URL` are overridden to service names (`db`, `redis`). Local `.env` values like `127.0.0.1` do not break containers.

Secrets stay in `.env` (gitignored). Do not commit real live keys.

### 1.2 Frontend (`frontend/.env`)

```bash
cd frontend
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Backend origin (`http://127.0.0.1:8000`) |
| `VITE_STRIPE_PUBLISHABLE_KEY` | `pk_test_…` for Stripe Elements (optional if using mock) |

### 1.3 Test vs live payment modes

| Provider | Test / sandbox | Live |
|----------|----------------|------|
| Stripe | `sk_test_…` + `pk_test_…` | `sk_live_…` + `pk_live_…` + live webhook secret |
| bKash | Sandbox base URL + sandbox credentials (in `.env.example`) | Live base URL + merchant live credentials |

Assessment / local review uses **test + sandbox** (and mock fallbacks when keys are empty).

---

## 2. Why ngrok is needed

Stripe and (optionally) bKash **webhook** servers must call your machine:

| Endpoint | Method |
|----------|--------|
| `/api/payments/webhooks/stripe/` | `POST` |
| `/api/payments/webhooks/bkash/` | `POST` |

Those URLs are not reachable from the internet at `http://127.0.0.1:8000`. **ngrok** opens a public HTTPS tunnel to your local Django port so providers can deliver events while you develop.

Alternative for Stripe only: `stripe listen --forward-to localhost:8000/api/payments/webhooks/stripe/` (Stripe CLI). ngrok works for **both** Stripe and bKash webhooks.

---

## 3. Local ngrok setup (step by step)

### 3.1 Install & authenticate

1. Install ngrok: https://ngrok.com/download  
2. Sign up and copy your authtoken  
3. Authenticate once:

```bash
ngrok config add-authtoken <YOUR_AUTHTOKEN>
```

### 3.2 Start the backend locally

Docker (recommended):

```bash
# from repo root
docker compose up --build
# API on http://127.0.0.1:8000
```

Or manual:

```bash
cd backend
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 3.3 Start the ngrok tunnel

```bash
ngrok http 8000
```

Example output:

```text
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the **HTTPS** forwarding URL (e.g. `https://abc123.ngrok-free.app`).

### 3.4 Allow the ngrok host in Django

Edit `backend/.env`:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,abc123.ngrok-free.app
```

Restart the API container / `runserver` so settings reload.

> Free ngrok URLs change every session unless you use a reserved domain. Update `ALLOWED_HOSTS` (and Stripe/bKash webhook URLs) when the host changes.

### 3.5 Configure Stripe webhooks via ngrok

**Option A — Stripe Dashboard (test mode)**

1. Developers → Webhooks → Add endpoint  
2. Endpoint URL: `https://abc123.ngrok-free.app/api/payments/webhooks/stripe/`  
3. Events: `payment_intent.succeeded`, `payment_intent.payment_failed` (and others you handle)  
4. Copy the signing secret `whsec_…` into:

```env
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Option B — Stripe CLI (no Dashboard URL needed)**

```bash
stripe listen --forward-to localhost:8000/api/payments/webhooks/stripe/
```

Use the printed `whsec_…` as `STRIPE_WEBHOOK_SECRET`. You can skip ngrok for Stripe-only webhook testing.

### 3.6 Configure bKash webhook / callback via ngrok

- **Browser callback (user return):** usually stays on the Vite frontend  
  `BKASH_CALLBACK_URL=http://localhost:5173/checkout`  
  (no ngrok required for the redirect return path when testing locally.)

- **Server webhook** (if your bKash merchant panel supports a notification URL):  
  `https://abc123.ngrok-free.app/api/payments/webhooks/bkash/`  

Optionally set `BKASH_WEBHOOK_SECRET` and send `X-Bkash-Signature: sha256=<hmac-hex>` over the raw body. Status is **always** re-verified via bKash Query Payment API.

### 3.7 Smoke-test the public tunnel

```bash
curl -i https://abc123.ngrok-free.app/api/docs/
```

You should get HTTP 200 (Swagger UI). For webhook POSTs, use Postman (`docs/EOPS.postman_collection.json`) against the ngrok base URL, or complete a real Stripe test payment and watch Django logs.

### 3.8 Typical local topology

```text
Browser  →  http://127.0.0.1:5173  (Vue)
Browser  →  http://127.0.0.1:8000  (API, same machine)

Stripe / bKash servers
         →  https://<ngrok>.ngrok-free.app
         →  localhost:8000  (tunnel)
         →  /api/payments/webhooks/...
```

---

## 4. Troubleshooting

| Issue | Fix |
|-------|-----|
| Django `DisallowedHost` | Add the exact ngrok hostname to `ALLOWED_HOSTS`, restart |
| Stripe `400` invalid signature | Refresh `STRIPE_WEBHOOK_SECRET`; use raw body (already handled in views) |
| ngrok browser interstitial | Use the ngrok agent / API headers, or paid plan; webhooks usually bypass the HTML warning |
| Tunnel works but webhooks silent | Confirm Dashboard/CLI points at `/api/payments/webhooks/stripe/` (trailing path matters) |
| Free URL expired | Restart `ngrok http 8000`, update `ALLOWED_HOSTS` + provider webhook URL |

---

## 5. Security notes

- Prefer **test/sandbox** keys with ngrok during assessment demos.
- Never commit live secrets or a long-lived production webhook secret into git.
- Keep `DEBUG=False` and strict `ALLOWED_HOSTS` for any shared/permanent tunnel.
