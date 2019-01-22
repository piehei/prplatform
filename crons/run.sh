#!/bin/sh


# get postgres usernames etc.
source /app/.envs/.local/.postgres

export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"

echo "starting fetch"

# this mgmt command fetches new submissions from APLUS api
python /app/manage.py retry_apicalls

echo "fetch finished"
