#!/bin/sh

# set -o errexit
# set -o pipefail
set -o nounset
set -o xtrace


# this will setup cronjobs that will call django mgmt commands
./crons/setup.sh

python manage.py migrate

while true; do
  echo "Restarting.........."
  python manage.py runserver_plus 0.0.0.0:8000
  sleep 2
done
