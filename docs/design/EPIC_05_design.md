# Epic 5 Design — Auth and User Access MVP

**Linear:** [LAL-9](https://linear.app/lalithshankar/issue/LAL-9/e05-auth-and-user-access-mvp)  
**Status:** Draft — awaiting Manager approval before implementation  
**Depends on:** Epic 2 (backend skeleton), Epic 4 (database foundation)  
**Canonical spec:** `user_story/evidence-fusion-post-edap-full/02_epics/EPIC_05_auth_and_user_access_mvp.md`

---

## 1. Goal & scope

### Delivers
- **Local username/password authentication** for development and early deployed environments.
- **Authenticated session contract** between React SPA and FastAPI (login, current-user resolution, protected routes).
- **User model with role/status fields** and FastAPI dependencies that expose `current_user` to endpoints and logging.
- **Extension hooks** for future RBAC and case-level access (Epic 6+), without implementing full permissions in this epic.

### Non-goals (explicit)
- Microsoft Entra External ID / OIDC integration (future epic).
- Admin UI for user management, password reset email, MFA, or SSO.
- Full RBAC enforcement or case-membership filtering (schema/hooks only).
- Multi-tenant isolation, org/team hierarchy, or production-grade account lifecycle.
- Audit UI (Epic 20); Epic 5 only ensures `user_id` is available for audit writes and structured logs.

---

## 2. Approach

### Chosen design: local credentials + signed JWT access tokens

1. Users stored in PostgreSQL (`users` table from Epic 4 placeholder, fleshed out in Epic 5).
2. Passwords hashed with **bcrypt** (via `passlib` or equivalent); never stored or logged in plaintext.
3. **Login** validates credentials and returns a short-lived **JWT access token** (HS256, signed with `SECRET_KEY`).
4. **Authenticated requests** send `Authorization: Bearer <token>`; a FastAPI dependency decodes the token and loads the user row.
5. **Frontend** keeps the access token in **React state / in-memory context** (not `localStorage`); lost on full page refresh → user re-logs in (acceptable for MVP dev).
6. **Auth provider abstraction** (`LocalAuthProvider` now; `EntraAuthProvider` later) so token validation and `get_current_user` do not hard-code local JWT logic in every router.

### Rejected alternatives

| Alternative | Why rejected for MVP |
|-------------|---------------------|
| **Server-side session table + HttpOnly cookie** | Strong CSRF story, but adds session store, logout invalidation, and CSRF token plumbing before Entra migration; cookies + SPA CORS are harder to test and debug locally. |
| **JWT in `localStorage`** | Simple, but increases XSS blast radius; in-memory token is sufficient for MVP and matches Bearer-header API style. |
| **Entra-first, skip local auth** | Blocks all development until Azure identity is wired; contradicts `DECISIONS_LOG.md` proposed decision: local auth first. |

### Sequencing note
Epic 5 does **not** use background workers or queues. All auth is synchronous request/response on the API process.

---

## 3. Data model & API contracts

### 3.1 `users` table (extends Epic 4 placeholder)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Stable identity for audit, cases, uploads |
| `email` | string, unique, not null | Login identifier (email-as-username for MVP) |
| `display_name` | string, not null | UI label |
| `password_hash` | string, not null | bcrypt; never exposed via API |
| `role` | enum, not null, default `analyst` | See §3.2 |
| `status` | enum, not null, default `active` | `active` \| `disabled` |
| `created_at` | timestamptz | From Epic 4 base mixin |
| `updated_at` | timestamptz | From Epic 4 base mixin |

**Indexes:** unique on `email`; index on `status` for admin queries later.

### 3.2 Role enum (MVP — stored, lightly enforced)

| Role | Intent (future) |
|------|-----------------|
| `analyst` | Default; upload/review evidence on assigned cases |
| `case_manager` | Create cases, assign members, edit case metadata |
| `admin` | User/role management (no UI in Epic 5) |

Epic 5 **stores** role and exposes it on `GET /auth/me`. Role-based route guards are **stubbed** (`require_roles` dependency exists but only used on a demo protected endpoint). Full enforcement deferred to Epic 6+.

### 3.3 Case access hook (schema stub — not enforced in Epic 5)

Prepare for Epic 6 without implementing membership CRUD:

```text
case_memberships (migration in Epic 5 or Epic 6 — see open questions)
  id            UUID PK
  case_id       UUID FK → cases.id
  user_id       UUID FK → users.id
  access_level  enum: viewer | contributor | manager
  created_at    timestamptz
  UNIQUE (case_id, user_id)
```

Epic 5 delivers **`check_case_access(user, case_id, min_level)`** as a dependency stub that:
- Today: returns `True` for any authenticated active user (permissive dev default).
- Epic 6: replaces body with membership lookup.

This satisfies Epic 6 story “cases I am allowed to access” without redesign.

### 3.4 Pydantic schemas (API-facing)

**`UserPublic`** (never includes `password_hash`):
```json
{
  "id": "uuid",
  "email": "analyst@example.com",
  "display_name": "Analyst One",
  "role": "analyst",
  "status": "active"
}
```

**`LoginRequest`:** `{ "email": string, "password": string }`  
**`LoginResponse`:** `{ "access_token": string, "token_type": "bearer", "expires_in": 1800 }`  
**`TokenPayload` (internal):** `{ "sub": "<user_id>", "role": "<role>", "exp": <unix>, "iat": <unix> }`

### 3.5 HTTP endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/login` | Public | Validate credentials; return JWT |
| `GET` | `/auth/me` | Bearer | Current user profile |
| `POST` | `/auth/logout` | Bearer | No-op for stateless JWT MVP; returns 204 (frontend clears token). Documented for future session invalidation. |
| `GET` | `/auth/protected/ping` | Bearer | Test-only protected route for AC verification (may remove before merge or keep as health-adjacent smoke test) |

**Public routes (no auth):** `/health`, `/auth/login`, OpenAPI docs in local only (see §5).

**Error shapes (consistent with FastAPI):**
- Invalid credentials → `401` with generic `{ "detail": "Invalid email or password" }` (no user enumeration).
- Missing/invalid token → `401` `{ "detail": "Not authenticated" }`.
- Disabled user → `403` `{ "detail": "Account disabled" }`.

### 3.6 Frontend contracts

- **`AuthProvider`** context: `{ user, token, login(), logout(), isAuthenticated, isLoading }`.
- **`LoginPage`**: email + password form; on success, store token in context and navigate to dashboard.
- **`ProtectedRoute`**: redirect to `/login` if unauthenticated.
- **`apiClient`**: attach `Authorization: Bearer` when token present; on `401`, clear auth and redirect to login.
- **Routes:** `/login` (public), `/` and future case routes (protected).

TanStack Query keys for `GET /auth/me` invalidate on login/logout.

### 3.7 Integration with existing logging (Epic 2)

After successful auth resolution in middleware or `get_current_user`, call:

```python
bind_log_context(user_id=str(current_user.id))
```

This satisfies Story 5.2 / Epic 2 logging AC: user ID attached when known. `clear_log_context()` already runs at request end in `main.py`.

---

## 4. Security & provenance

### 4.1 Secret handling
| Setting | `APP_ENV=local` | `APP_ENV=deployed` |
|---------|-----------------|---------------------|
| `SECRET_KEY` | `.env` placeholder; dev-only | **Required** from Azure Key Vault via Managed Identity |
| JWT signing | HS256 with `SECRET_KEY` | Same algorithm; production key must be high-entropy |
| Password hashes | bcrypt, cost factor ≥ 12 | Same |

Startup validation (deployed): fail fast if `SECRET_KEY` is default/weak or Key Vault unreachable.

### 4.2 Token policy (MVP)
- Access token TTL: **30 minutes** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- No refresh token in Epic 5; re-login on expiry.
- Claims: `sub` (user id), `role`, `exp`, `iat` only — no PII in JWT payload beyond id/role.
- Algorithm: **HS256** for local auth; Entra migration will use RS256 + JWKS via separate provider (no change to endpoint handlers).

### 4.3 Password & account safety
- bcrypt hashing; constant-time comparison via library.
- Login failures return identical message for unknown email vs wrong password.
- `status=disabled` users cannot obtain tokens; existing tokens rejected at `get_current_user`.
- Passwords and tokens covered by existing log redaction in `app/core/logging.py`.

### 4.4 Transport & CORS
- Local: HTTP acceptable; deployed: **HTTPS only** (enforced at ingress, Epic 21).
- CORS already uses `allow_credentials=True`; Bearer header avoids cookie CSRF for MVP.
- Rate limiting on `/auth/login`: **recommended** but optional for Epic 5 (see open questions).

### 4.5 Provenance & audit hooks
- Every authenticated request resolves `user_id` before business logic.
- `audit_service.write(..., user_id=current_user.id)` callable from Epic 4 helper without auth changes.
- Evidence upload (Epic 7) will record uploader identity via the same `current_user` dependency.

### 4.6 Local dev bootstrap
- Alembic migration creates `users` table.
- **`scripts/seed_local_users.py`** (or pytest fixture factory) creates default dev users, e.g.:
  - `analyst@local.dev` / known dev password (documented in README, not committed)
- Idempotent seed: safe to re-run.

---

## 5. APP_ENV: local vs deployed

| Concern | Local | Deployed |
|---------|-------|----------|
| Auth mechanism | Local email/password + JWT | **Same** for MVP (Entra later) |
| User provisioning | Seed script + manual SQL | **Open question:** seed vs one-time bootstrap admin |
| `SECRET_KEY` source | `.env` | Azure Key Vault |
| OpenAPI `/docs` | Enabled | Disabled or auth-gated |
| Token storage (frontend) | In-memory context | Same |
| Default passwords | Allowed for dev users | **Must not** ship default credentials |

Deployed MVP still requires login for all non-health routes; there is no anonymous evidence path per `PROJECT_PLAN.md` non-negotiables.

---

## 6. Module layout (implementation guide — not built until approved)

```
backend/app/
  api/auth.py              # login, me, logout, protected ping
  core/security.py         # hash/verify password, create/decode JWT
  core/auth_deps.py        # get_current_user, require_roles, check_case_access stub
  core/auth_provider.py    # LocalAuthProvider protocol + impl
  models/user.py           # User ORM + role/status enums
  schemas/user.py          # UserPublic, LoginRequest, LoginResponse
  services/auth_service.py # authenticate, issue_token, get_user_by_id

frontend/src/
  pages/Login.tsx
  context/AuthContext.tsx
  components/ProtectedRoute.tsx
  lib/apiClient.ts         # Bearer injection + 401 handling
```

New backend dependencies (Epic 5 PR): `python-jose[cryptography]` or `PyJWT`, `passlib[bcrypt]`, plus Epic 4 deps (`sqlalchemy`, `alembic`, `psycopg`).

---

## 7. Test strategy

| Acceptance criterion | Verification |
|---------------------|--------------|
| Valid credentials → authenticated session/token | Pytest: POST `/auth/login` with seeded user → 200 + JWT; decode and assert `sub`. Frontend Vitest: login success sets context. |
| Invalid credentials → safe error | Pytest: wrong password → 401, generic message, no user leak. |
| Unauthenticated → protected route rejected | Pytest: GET `/auth/me` and `/auth/protected/ping` without header → 401. Frontend: `ProtectedRoute` redirects. |
| User has role/status fields | Pytest: model + migration assert columns; GET `/auth/me` returns role/status. |
| Current user available to endpoint | Pytest: authenticated `/auth/me` returns correct user; dependency injects user into test router. |
| User ID attachable for audit/logs | Pytest: authenticated request log line includes `user_id` (extend `test_logging` pattern from Epic 2). |
| Disabled user blocked | Pytest: login and token use for disabled user → 403. |
| Secrets not in responses/logs | Pytest: login response and health never expose `password_hash` or raw token in logs (redaction test). |

Test DB: use Epic 4 pytest fixtures (transaction rollback or test database); no production credentials.

---

## 8. Risks

| Risk | Mitigation |
|------|------------|
| JWT in memory lost on refresh | Accept for MVP; refresh tokens or HttpOnly cookies in Entra/hardening epic. |
| Permissive `check_case_access` stub hides auth bugs until Epic 6 | Document clearly; add Epic 6 AC to replace stub; optional feature flag `STRICT_CASE_ACCESS`. |
| Epic 4 not merged when Epic 5 starts | Epic 5 branch must rebase on Epic 4; design aligns with Epic 4 `users` placeholder. |
| Weak local `SECRET_KEY` committed | `.env.example` only; CI/gitleaks; deployed startup validation. |
| Entra migration rewrites auth | Provider abstraction + thin `get_current_user` dependency limit blast radius. |

---

## 9. Assumptions

1. **Email is the login identifier** (no separate username column for MVP).
2. Epic 4 delivers SQLAlchemy base, UUID PKs, timestamps, and a minimal `users` placeholder table.
3. `SECRET_KEY` already exists in settings (`backend/app/core/config.py`); Epic 5 adds token settings derived from it.
4. Frontend Epic 3 shell provides routing and API client patterns to extend.
5. `DECISIONS_LOG.md` proposed row “MVP auth: Local username/password first; Entra External ID later” will be approved.

---

## 10. Open questions for Manager approval

1. **Token delivery:** Approve **Bearer JWT in memory** (recommended) vs **HttpOnly cookie session** for MVP?
2. **Case membership table:** Create `case_memberships` migration in Epic 5 (empty, hook only) or defer table creation to Epic 6?
3. **Deployed user bootstrap:** How are first users created in `APP_ENV=deployed` before admin UI exists? Options: (a) one-time CLI seed, (b) env-var bootstrap admin on first startup, (c) block deployed auth until Entra.
4. **Login rate limiting:** Required in Epic 5 or acceptable as fast-follow before any public deployment?
5. **Default dev credentials:** Approve documented seed users (`analyst@local.dev`, `admin@local.dev`) with a shared dev password in README (never in repo)?
6. **Role enforcement scope:** Confirm Epic 5 only **stores/exposes** roles; enforcement waits until Epic 6 case APIs.
7. **OpenAPI in deployed:** Disable `/docs` entirely in deployed, or require auth?
8. **Entra timeline:** Confirm local auth remains valid in deployed until Entra epic is scheduled (affects Q3).

---

**Next step:** Manager approves or amends this design → Builder implements on branch `epic-5-auth-and-user-access-mvp` → QA verifies acceptance criteria → PR for human merge.

**Do not implement Epic 5 until this document is approved.**
