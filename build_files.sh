#!/bin/bash
set -e

python manage.py check
python manage.py collectstatic --noinput
