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
