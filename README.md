# EventCore San Isidro

EventCore is a Django-based barangay event management system for Barangay San Isidro, Surigao City, Surigao del Norte.

## Features

- Event planning with category, venue, schedule, budget, organizer, status, and public/private visibility
- Attendee registry with resident/guest tracking, roles, confirmation, and check-in status
- Resource and logistics tracking for chairs, sound systems, tents, vehicles, supplies, and assigned custodians
- Budget line items with planned, approved, released, and liquidated status
- Announcements for public advisories and event notices
- Dashboard metrics for upcoming events, active attendees, resource readiness, and budget totals
- Clean responsive interface with a dedicated EventCore command center
- Django admin support for all records
- PostgreSQL database configuration, not SQLite

## Setup

1. Create and activate a virtual environment.
2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your PostgreSQL credentials.
4. Create the PostgreSQL database named in `DB_NAME`.
5. Run:

```powershell
python manage.py migrate
python manage.py seed_eventcore
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Deploying to Render

This project includes a `render.yaml` Blueprint. Push the project to GitHub, then create a new Render Blueprint from the repository.

Render will create:

- a Python web service
- a PostgreSQL database
- generated `SECRET_KEY`
- `DATABASE_URL` connected to the database

Manual Render settings, if you deploy without the Blueprint:

- Build command: `bash build.sh`
- Start command: `gunicorn config.wsgi:application`
- Python version: `3.13.5`
- Environment variables:
  - `DEBUG=False`
  - `SECRET_KEY=<generate a secure value>`
  - `ALLOWED_HOSTS=.onrender.com`
  - `DATABASE_URL=<your Render PostgreSQL internal connection string>`

After the first deploy, create an admin user from Render Shell:

```bash
python manage.py createsuperuser
```
