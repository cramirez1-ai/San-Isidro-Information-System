# Barangay San Isidro Information System

A Django project for Barangay San Isidro, Surigao City, Surigao del Norte.

## Features

- Dashboard with barangay profile and system totals
- Resident and household records
- Barangay officials directory
- Barangay services and service requests
- Announcements
- Blotter incident records
- Single administrator workspace

## Barangay Reference Data

- Barangay: San Isidro
- City: Surigao City
- Province: Surigao del Norte
- PSGC code: 1606724039
- Correspondence code: 166724039
- Urban/Rural class: Rural
- 2020 Census population: 629

## Run Locally

```powershell
python manage.py migrate
python manage.py seed_initial_data
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Create the administrator account:

```powershell
$env:ADMIN_USERNAME="admin"
$env:ADMIN_EMAIL="admin@sanisidro.local"
$env:ADMIN_PASSWORD="change-this-password"
python manage.py setup_admin
```

Admin URL:

```text
http://127.0.0.1:8000/admin/
```

## Notes

The seed command adds starter services and one clearly marked sample announcement. Replace sample content with official barangay data before real use. Self-registration is disabled; only the configured administrator account can use the workspace.

## Deploy on Render

This project includes a Render-ready structure:

- `render.yaml` defines the web service, PostgreSQL database, build command, and start command.
- `build_files.sh` runs Django deployment checks and collects static files.
- `gunicorn` serves the Django app.
- `whitenoise` serves static files in production.
- `.python-version` pins Python 3.12 for Django 6.

Set `ADMIN_PASSWORD` in Render before the first deploy. Render will generate `SECRET_KEY` and connect `DATABASE_URL` automatically from `render.yaml`.

Important Render environment variables:

```text
SECRET_KEY=your-secure-secret-key
DEBUG=False
DATABASE_URL=your-postgres-database-url
ALLOWED_HOSTS=.onrender.com,your-domain.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://your-domain.com
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@sanisidro.local
ADMIN_PASSWORD=your-secure-admin-password
```

Use PostgreSQL for production. SQLite is only for local development.
