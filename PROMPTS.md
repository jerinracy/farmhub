Task 01 — Project Scaffold

Create a new Django project called "farmhub" with the following structure:

farmhub/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── farms/
│   ├── farmers/
│   ├── cattle/
│   ├── activities/
│   ├── production/
│   └── reports/
├── manage.py
└── requirements.txt

Requirements:
- Use Django 5.x and Django REST Framework.
- Each folder under apps/ should be a proper Django app (with apps.py, models.py, admin.py, etc.), created via `startapp`, then moved into the apps/ package. Make sure each app's apps.py uses the correct dotted path (e.g. "apps.accounts") so Django can find them.
- Add "apps" to sys.path handling in manage.py/config/settings.py if needed so `apps.accounts` etc. import cleanly.
- In config/settings.py add: INSTALLED_APPS entries for rest_framework, rest_framework_simplejwt, rest_framework_simplejwt.token_blacklist, django_filters, corsheaders, and all seven local apps.
- Use python-decouple to read SECRET_KEY, DEBUG, DATABASE_URL (or individual DB vars) from a .env file. Create a .env.example with placeholder values.
- Configure PostgreSQL as the database backend using psycopg2-binary, reading credentials from .env.
- Add a requirements.txt with: Django, djangorestframework, djangorestframework-simplejwt, django-filter, psycopg2-binary, python-decouple, django-cors-headers, drf-spectacular, django-extensions.
- Set up a basic config/urls.py with an empty api/ prefix ready for future app includes, and a /api/docs/ route using drf-spectacular's SpectacularAPIView + SpectacularSwaggerView.
- Confirm the project runs with `python manage.py runserver` without errors (no models yet, so migrations will be empty at this point).

Do not create any models yet — this task is scaffolding only.

Task 02 — Custom User Model & Roles

In apps/accounts, implement the custom User model for FarmHub.

Requirements:
- User extends AbstractUser.
- Add a `role` field: CharField with choices SUPERADMIN, AGENT, FARMER (use a TextChoices inner class named Role).
- Add `phone_number` (CharField, blank=True, max_length=20).
- Add `created_by` — ForeignKey to "self", null=True, blank=True, on_delete=SET_NULL, related_name="created_users".
- Add `created_at` — DateTimeField(auto_now_add=True).
- Register this as AUTH_USER_MODEL = "accounts.User" in config/settings.py.
- Create and apply the initial migration.
- Register User in admin.py using Django's UserAdmin as a base, extended to show role, phone_number, created_by, is_active in the list display and fieldsets.
- Create a management command `seed_superadmin` (apps/accounts/management/commands/seed_superadmin.py) that creates a default SuperAdmin user from env vars (SUPERADMIN_USERNAME, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD) if one doesn't already exist, and sets role=SUPERADMIN, is_staff=True, is_superuser=True.

Verify: python manage.py makemigrations && migrate runs cleanly, and python manage.py seed_superadmin creates a working superuser.

Task 03 — JWT Authentication Endpoints

Set up JWT authentication for FarmHub using djangorestframework-simplejwt.

Requirements:
- In config/settings.py, set REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] to JWTAuthentication, and DEFAULT_PERMISSION_CLASSES to IsAuthenticated.
- Add a SIMPLE_JWT config dict: ACCESS_TOKEN_LIFETIME=1 hour, REFRESH_TOKEN_LIFETIME=7 days, ROTATE_REFRESH_TOKENS=True, BLACKLIST_AFTER_ROTATION=True.
- In apps/accounts, create a custom TokenObtainPairSerializer subclass ("CustomTokenObtainPairSerializer") that adds `role`, `username`, and `id` claims into the returned token response (not just the JWT payload — also in the response body alongside access/refresh).
- Create views: CustomTokenObtainPairView (uses the serializer above), TokenRefreshView (default from simplejwt), and a LogoutView that blacklists the refresh token on POST.
- Wire up urls in apps/accounts/urls.py:
  - POST /api/auth/login/
  - POST /api/auth/refresh/
  - POST /api/auth/logout/
- Include these in config/urls.py under /api/auth/.
- Write a quick apps/accounts/tests/test_auth.py with a test that logs in a seeded user and asserts access+refresh tokens are returned with the expected custom claims.

Verify: running the seed_superadmin command from Task 02, then POSTing valid credentials to /api/auth/login/ returns access, refresh, role, username, id.

Task 04 — Role-Based Permission Classes

In apps/accounts/permissions.py, implement reusable DRF permission classes for FarmHub:

- IsSuperAdmin: allows only request.user.role == "SUPERADMIN"
- IsAgent: allows only request.user.role == "AGENT"
- IsFarmer: allows only request.user.role == "FARMER"
- IsSuperAdminOrAgent: allows SUPERADMIN or AGENT
- IsAuthenticatedAndActive: base check that user.is_authenticated and user.is_active

All classes should extend rest_framework.permissions.BasePermission and implement has_permission. Add docstrings explaining each class's intended use per the FarmHub role spec (SuperAdmin > Agent > Farmer hierarchy).

Also add a small pytest suite (apps/accounts/tests/test_permissions.py) using factory-created users of each role, asserting each permission class allows/denies correctly for a dummy APIView.

Do not wire these into any viewsets yet — this task only creates and tests the permission classes in isolation.

Task 05 — Agent Management (SuperAdmin creates Agents)

Implement Agent management in apps/accounts.

Requirements:
- Create an AgentSerializer (ModelSerializer on User) exposing: id, username, email, phone_number, role, created_by, created_at. On create, force role="AGENT" and set is_active=True, hash the password properly (accept a write-only `password` field).
- Create AgentViewSet (ModelViewSet) restricted to IsAuthenticated + IsSuperAdmin for all actions.
  - queryset: User.objects.filter(role="AGENT")
  - On create, set created_by=request.user.
- Register the viewset under /api/agents/ via a DRF router, included in config/urls.py.
- Add pytest tests (apps/accounts/tests/test_agent_api.py):
  - SuperAdmin can create an agent (201).
  - Agent or Farmer attempting to create an agent gets 403.
  - SuperAdmin can list/retrieve/update/deactivate agents.

Verify with a manual curl/Postman flow: login as seeded superadmin, POST /api/agents/ with username/email/password/phone_number, confirm role=AGENT is set automatically and the new agent can log in via /api/auth/login/.

Task 06 — Farm Model & Farm Management

Create the apps/farms app's Farm model and CRUD API.

Model (apps/farms/models.py):
- name (CharField, max_length=150)
- location (CharField, max_length=255)
- agent (ForeignKey to accounts.User, on_delete=SET_NULL, null=True, related_name="managed_farms", limit_choices_to={"role": "AGENT"})
- created_by (ForeignKey to accounts.User, on_delete=SET_NULL, null=True, related_name="farms_created")
- is_active (BooleanField, default=True)
- created_at / updated_at (auto_now_add / auto_now)

API:
- FarmSerializer: full fields, with agent as a writable PrimaryKeyRelatedField restricted to queryset User.objects.filter(role="AGENT"), plus a read-only nested `agent_detail` (id, username) for display.
- FarmViewSet (ModelViewSet):
  - Only SuperAdmin can create/delete farms.
  - SuperAdmin can update any farm; an Agent can update only farms where farm.agent == request.user (use get_queryset + has_object_permission via a custom permission class IsSuperAdminOrOwningAgent in apps/farms/permissions.py).
  - get_queryset: SuperAdmin sees all farms; Agent sees only farms they manage; Farmer sees only their own farm (join through farmer profile — for now, if FarmerProfile doesn't exist yet, just return none for Farmer role, we'll fix in Task 07).
- Register under /api/farms/ via router.
- Add pytest tests covering: SuperAdmin creates farm + assigns agent; Agent cannot create a farm (403); Agent can PATCH their own farm but not another agent's farm (403).

Run makemigrations/migrate and confirm admin.py registers Farm with list_display showing name, location, agent, is_active.

Task 07 — Farmer Onboarding (User + FarmerProfile)

Create the apps/farmers app: FarmerProfile model and onboarding API.

Model (apps/farmers/models.py):
- user (OneToOneField to accounts.User, on_delete=CASCADE, related_name="farmer_profile", limit_choices_to={"role": "FARMER"})
- farm (ForeignKey to farms.Farm, on_delete=CASCADE, related_name="farmers")
- national_id (CharField, max_length=50, blank=True)
- address (CharField, max_length=255, blank=True)
- onboarded_by (ForeignKey to accounts.User, on_delete=SET_NULL, null=True, related_name="onboarded_farmers")
- joined_at (DateTimeField, auto_now_add=True)

API:
- FarmerOnboardSerializer: accepts username, email, password, phone_number (for the User) PLUS farm (FK id), national_id, address (for the profile) in one payload. Its `create()` method must, in a single db transaction (use transaction.atomic):
  1. Create the User with role="FARMER".
  2. Create the FarmerProfile linked to that user, farm, and onboarded_by=request.user.
- FarmerListSerializer: read-only, nested — shows user (id, username, email, phone_number), farm (id, name), national_id, address, joined_at.
- FarmerViewSet (ModelViewSet):
  - create: allowed for SuperAdmin and Agent. If the requester is an Agent, validate that the submitted `farm` is one they manage (farm.agent == request.user) — else return 400 with a clear error.
  - list/retrieve: SuperAdmin sees all; Agent sees farmers on farms they manage; Farmer sees only their own profile.
  - update/delete: SuperAdmin only, plus Agent limited to farmers on their managed farms.
  - Use FarmerOnboardSerializer for create, FarmerListSerializer for list/retrieve.
- Register under /api/farmers/ via router.
- Now go back and fix FarmViewSet.get_queryset from Task 06 so a Farmer sees their own farm by looking up request.user.farmer_profile.farm.

Add pytest tests: SuperAdmin onboards a farmer onto any farm (201, both User and FarmerProfile created); Agent onboards a farmer only onto their own managed farm (403 if wrong farm); Farmer role cannot onboard farmers (403); the new farmer can log in via /api/auth/login/.

Task 08 — Cow Model & Enrollment

Create the apps/cattle app: Cow model and enrollment API.

Model (apps/cattle/models.py):
- tag_id (CharField, max_length=50, unique=True)
- farm (ForeignKey to farms.Farm, on_delete=CASCADE, related_name="cows")
- farmer (ForeignKey to accounts.User, on_delete=CASCADE, related_name="cows", limit_choices_to={"role": "FARMER"})
- breed (CharField, max_length=100)
- gender (CharField, max_length=1, choices=[("M","Male"),("F","Female")])
- date_of_birth (DateField, null=True, blank=True)
- is_active (BooleanField, default=True)
- created_at (auto_now_add=True)
- Meta.indexes: index on (farm, farmer)
- Override save() so that if `farm` is not explicitly set, it's auto-populated from farmer.farmer_profile.farm — keep them in sync.

API:
- CowSerializer: all fields; farmer is writable but validated so a Farmer can only set farmer=request.user (i.e. farmer field is read-only/forced for Farmer role, but selectable for Agent/SuperAdmin from farmers on their managed farm(s)).
- CowViewSet (ModelViewSet):
  - create: Farmer (only their own cows), Agent (any farmer on a farm they manage), SuperAdmin (any).
  - get_queryset: SuperAdmin → all; Agent → Cow.objects.filter(farm__agent=request.user); Farmer → Cow.objects.filter(farmer=request.user).
  - On create as Farmer, force farmer=request.user and farm=request.user.farmer_profile.farm regardless of payload.
- Register under /api/cows/ via router.
- Add pytest tests: Farmer enrolls their own cow (201, farm auto-set correctly); Farmer cannot enroll a cow under a different farmer's name (should be forced/ignored, not 403 — verify the forced override); Agent enrolls a cow for a farmer on their managed farm (201); Agent cannot enroll a cow for a farmer outside their managed farms (403 or 400); unique tag_id constraint returns 400 on duplicate.

Register Cow in admin.py with list_display: tag_id, breed, gender, farm, farmer, is_active.

Task 09 — Cow Activity Logging (Vaccination / Birth / Health Check)

Create the apps/activities app: CowActivity model and logging API.

Model (apps/activities/models.py):
- cow (ForeignKey to cattle.Cow, on_delete=CASCADE, related_name="activities")
- activity_type (CharField, choices=VACCINATION, BIRTH, HEALTH_CHECK, OTHER)
- date (DateField)
- notes (TextField, blank=True)
- details (JSONField, default=dict, blank=True)  — for flexible per-type fields (e.g. vaccine name/dose for VACCINATION)
- recorded_by (ForeignKey to accounts.User, on_delete=SET_NULL, null=True)
- created_at (auto_now_add=True)
- Meta.indexes: index on (cow, activity_type, date)

API:
- CowActivitySerializer: all fields; cow is a writable FK but must belong to a cow the requester can access (see queryset scoping below); recorded_by is set automatically from request.user, not client-writable.
- Nest this under the cow, i.e. routes:
  - GET/POST /api/cows/{cow_pk}/activities/
  - GET/PATCH/DELETE /api/cows/{cow_pk}/activities/{id}/
  Use a nested router (drf-nested-routers is fine to add to requirements.txt if simplest, or implement manually by overriding get_queryset/perform_create to filter by the cow_pk URL kwarg — your choice, pick the simpler one and stick to it consistently).
- Permission/queryset rules: Farmer can only log/view activities for cows where cow.farmer == request.user; Agent can only log/view activities for cows on farms they manage; SuperAdmin sees all.
- On create, validate the cow_pk in the URL matches a cow the requester is authorized for (404 if not visible, not 403 — avoid leaking existence).

Add pytest tests: Farmer logs a vaccination for their own cow (201); Farmer cannot log an activity for another farmer's cow (404); Agent logs a health check for a cow on their managed farm (201); listing activities for a cow returns them ordered by -date.

Register CowActivity in admin.py with list_display: cow, activity_type, date, recorded_by.

Task 10 — Daily Milk Production Records

Create the apps/production app: MilkProduction model and recording API.

Model (apps/production/models.py):
- cow (ForeignKey to cattle.Cow, on_delete=CASCADE, related_name="milk_records")
- farm (ForeignKey to farms.Farm, on_delete=CASCADE, related_name="milk_records")  — denormalized, auto-set from cow.farm on save
- farmer (ForeignKey to accounts.User, on_delete=CASCADE, related_name="milk_records")  — denormalized, auto-set from cow.farmer on save
- date (DateField)
- quantity_liters (DecimalField, max_digits=6, decimal_places=2)
- session (CharField, choices=[("MORNING","Morning"),("EVENING","Evening")], default="MORNING")
- recorded_at (auto_now_add=True)
- Meta.unique_together: (cow, date, session)
- Meta.indexes: (farm, date) and (farmer, date)
- Override save() to auto-populate farm/farmer from the linked cow if not already set.

API:
- MilkProductionSerializer: cow is writable (validated against requester's accessible cows, same pattern as Task 09); date, quantity_liters, session are writable; farm/farmer are read-only/auto-derived, not client-writable.
- Nest under cow like activities: /api/cows/{cow_pk}/milk-records/ (GET, POST, PATCH, DELETE).
- Same visibility rules as Task 09 (Farmer → own cows only, Agent → managed farms, SuperAdmin → all).
- On duplicate (cow, date, session), return a clean 400 with a message like "Milk record already exists for this cow, date, and session."

Add pytest tests: Farmer records morning milk for their own cow (201); duplicate same cow/date/session returns 400; Agent records milk for a cow on their managed farm (201); Farmer cannot record milk for another farmer's cow (404).

Register MilkProduction in admin.py with list_display: cow, farm, farmer, date, session, quantity_liters.


Task 11 
Restructure the FarmHub repository into a monorepo with two independent services, and replace the Django-based reports app with a standalone read-only FastAPI reporting service.

PART A — Repo restructure

Target layout:

FarmHub/
├── core/                          # existing Django project, moved here as-is
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── farms/
│   │   ├── farmers/
│   │   ├── cattle/
│   │   ├── activities/
│   │   └── production/            # NOTE: apps/reports is being removed in Part B
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── reporting/                     # new FastAPI service
│   └── (see Part B)
├── README.md                      # top-level, describes both services
└── docker-compose.yml             # optional: run both services + shared Postgres

Steps:
1. Move every existing Django file/folder (config/, apps/, manage.py, requirements.txt, .env.example, pytest config, etc.) into a new core/ directory at the repo root, preserving git history if possible (use `git mv`).
2. Fix all import paths, INSTALLED_APPS dotted paths, and any hardcoded relative paths that assumed the project root — nothing under core/ should reference paths above core/.
3. Update any CI config, Dockerfiles, or run scripts to `cd core` (or use `--project-directory`) before invoking Django management commands.
4. Delete the apps/reports app entirely from core/ (models — it had none — views, serializers, urls, tests) and remove its router registration from core/config/urls.py and its entry from INSTALLED_APPS. Reporting now lives entirely in the reporting/ FastAPI service.
5. Add a top-level README.md explaining the two-service split: core/ = Django DRF (auth, farms, farmers, cows, activities, production — all writes), reporting/ = FastAPI (read-only aggregated reports, reads the same Postgres database).

PART B — FastAPI reporting service

Create reporting/ as an independent FastAPI project:

reporting/
├── app/
│   ├── main.py                    # FastAPI app instance, router includes, startup
│   ├── config.py                  # pydantic-settings: DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM
│   ├── db.py                      # SQLAlchemy async engine + session dependency
│   ├── models.py                  # SQLAlchemy Core/ORM models mirroring Django tables — READ ONLY, no migrations owned here
│   ├── schemas.py                 # Pydantic response models for report payloads
│   ├── auth.py                    # JWT verification + current-user dependency
│   ├── dependencies.py            # role-check dependencies (require_superadmin, require_agent_or_superadmin, etc.)
│   └── routers/
│       └── reports.py             # the three report endpoints
├── requirements.txt
├── .env.example
└── alembic/ (optional — see note below)

Requirements:

1. Database access:
   - reporting/ connects to the SAME PostgreSQL database core/ writes to. Use SQLAlchemy (async, with asyncpg) purely for SELECT queries — this service must never write.
   - In app/models.py, define SQLAlchemy models for exactly the tables needed: users (accounts_user — need id, username, role for report labels), farms_farm, cattle_cow, production_milkproduction. Map table names explicitly with __tablename__ to match Django's app_label_modelname convention (e.g. "accounts_user", "farms_farm", "cattle_cow", "production_milkproduction"). Only include the columns actually needed for reporting — do not replicate full Django schemas.
   - Do NOT generate Alembic migrations that create/alter these tables — Django owns the schema. If you add Alembic, configure it as inspect-only / no autogenerate against these tables, or skip Alembic entirely and just reflect tables at runtime with SQLAlchemy's Table(..., autoload_with=engine) if that's simpler.

2. Auth (JWT interop with Django SimpleJWT):
   - Django's djangorestframework-simplejwt issues HS256 JWTs signed with Django's SECRET_KEY. reporting/ must verify tokens using the SAME secret and algorithm — read JWT_SECRET_KEY and JWT_ALGORITHM (default "HS256") from reporting/.env, and document clearly in .env.example that JWT_SECRET_KEY MUST match core/'s Django SECRET_KEY.
   - In app/auth.py, implement a dependency get_current_user(token: str = Depends(oauth2_scheme)) that decodes the JWT with python-jose or PyJWT, extracts user id/username/role claims (the same custom claims added back in Task 03's CustomTokenObtainPairSerializer), and returns a small Pydantic CurrentUser object. Raise HTTP 401 on invalid/expired tokens.
   - In app/dependencies.py, build require_role(*roles) style dependencies (or individual require_superadmin, require_agent_or_superadmin) that raise HTTP 403 if current_user.role isn't allowed.
   - No login/refresh endpoints here — reporting/ only ever verifies tokens issued by core/'s /api/auth/login/.

3. Endpoints (mirror Task 11's spec exactly, same permission rules, but as FastAPI routes under reporting's own app):
   - GET /reports/farm/{farm_id}?date_from=&date_to=
     - Allowed: SuperAdmin, or the Agent who manages that farm (check farms_farm.agent_id against current_user.id).
     - Returns: farm id/name, total_liters, record_count, per-cow breakdown.
   - GET /reports/farmer/{farmer_id}?date_from=&date_to=
     - Allowed: SuperAdmin, the managing Agent, or the Farmer themself.
     - Returns: farmer id/username, farm name, total_liters, record_count, per-cow breakdown.
   - GET /reports/summary?date_from=&date_to=
     - SuperAdmin only.
     - Returns: system-wide total_liters plus per-farm breakdown ordered by total_liters descending.
   - Validate date_from/date_to as ISO dates (FastAPI + Pydantic handles this natively via `date` type query params) — return 422 automatically on bad format, no manual parsing needed.
   - Return 404 (not 403) when the target farm_id/farmer_id doesn't exist or isn't visible to the requester's role — same information-hiding rule as Task 11.
   - Use SQLAlchemy aggregate queries (func.sum, group by) equivalent to the Django ORM aggregation from Task 11 — same totals, same per-cow/per-farm breakdowns.

4. App wiring:
   - app/main.py creates the FastAPI() instance, includes the reports router under a version prefix (e.g. /api/v1), and adds a GET /health endpoint (no auth) returning {"status": "ok"}.
   - Add CORS middleware configured the same way as core/'s (allowed origins from .env).
   - Add automatic OpenAPI docs (FastAPI gives this for free at /docs) — no extra work needed, just confirm it renders and every endpoint has a clear summary/description and documented query params.

5. requirements.txt for reporting/: fastapi, uvicorn[standard], sqlalchemy>=2.0, asyncpg, pydantic-settings, python-jose[cryptography] (or pyjwt), python-dotenv.

6. Tests: reporting/tests/ using pytest + httpx.AsyncClient against the FastAPI app, with a test Postgres database seeded via SQLAlchemy directly (bypass Django). Cover: valid SuperAdmin token gets /reports/summary (200); Agent token gets /reports/farm/{id} only for their own farm (200) and 404 for another agent's farm; Farmer token gets /reports/farmer/{their_id} (200) and 403/404 for someone else's; expired/invalid JWT returns 401; date range filtering narrows totals correctly.

7. Confirm both services can run side by side locally (core/ on :8000, reporting/ on :8001) against the same local Postgres instance, and that a JWT obtained from POST core:8000/api/auth/login/ is accepted by reporting:8001/api/v1/reports/summary.

Do not touch core/'s accounts, farms, farmers, cattle, activities, or production apps in this task beyond the apps/reports removal described in Part A — this task is structural + the new reporting service only.

Task 12 
Final polish pass on FarmHub before calling the MVP done.

Requirements:
- Confirm drf-spectacular is fully wired: /api/schema/ and /api/docs/ (Swagger UI) return valid output covering all endpoints from Tasks 03–11. Add basic OpenAPI tags per app (accounts, farms, farmers, cattle, activities, production, reports) using @extend_schema_view or view docstrings.
- Configure django-cors-headers in config/settings.py: CORS_ALLOWED_ORIGINS read from .env (comma-separated), default to allowing localhost:3000 and localhost:5173 for dev.
- Add a root /api/health/ endpoint (simple APIView, no auth) returning {"status": "ok"}.
- Review every viewset created in Tasks 05–11 and confirm each has an explicit `permission_classes` — no viewset should be relying only on the global DEFAULT_PERMISSION_CLASSES if it needs role restriction.
- Add pagination: set REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] to PageNumberPagination with PAGE_SIZE=20 globally.
- Run the full pytest suite across all apps and fix any failing tests.
- Generate a README.md summarizing: setup steps (.env, migrate, seed_superadmin), the role model, and a table of all endpoints with required roles.

This is the last task in the MVP build — after this, FarmHub should be a working, documented, role-secured DRF backend covering SuperAdmin/Agent/Farmer workflows for farms, farmer onboarding, cow enrollment, activity logging, milk production, and reporting.