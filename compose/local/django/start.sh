#!/bin/sh

# set -o errexit
# set -o pipefail
set -o nounset
set -o xtrace

python manage.py migrate

while true; do
  echo "Restarting.........."
  python manage.py runserver_plus 0.0.0.0:8000
  sleep 2
done
