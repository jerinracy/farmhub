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

