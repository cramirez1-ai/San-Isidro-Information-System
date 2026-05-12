# Barangay San Isidro Information System

A Django project for Barangay San Isidro, Surigao City, Surigao del Norte.

## Features

- Dashboard with barangay profile and system totals
- Resident and household records
- Barangay officials directory
- Barangay services and service requests
- Announcements
- Blotter incident records
- Django admin support

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

Create an admin account:

```powershell
python manage.py createsuperuser
```

Admin URL:

```text
http://127.0.0.1:8000/admin/
```

## Notes

The seed command adds starter services and one clearly marked sample announcement. Replace sample content with official barangay data before real use.

## Deploy on Vercel

This project includes a Vercel-ready structure:

- `vercel.json` configures install, build, and dev commands.
- `build_files.sh` runs `collectstatic` and migrations during deployment.
- `.python-version` pins Python 3.12 for Django 6.
- `.vercelignore` keeps local files out of the deployment bundle.

Set these environment variables in Vercel Project Settings:

```text
SECRET_KEY=your-secure-secret-key
DEBUG=False
DATABASE_URL=your-postgres-database-url
ALLOWED_HOSTS=.vercel.app,your-domain.com
CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://your-domain.com
```

Use an external PostgreSQL database for production. SQLite is only for local development.
