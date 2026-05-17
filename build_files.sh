#!/bin/bash
set -e

pip install -r requirements.txt
python manage.py check
python manage.py collectstatic --noinput