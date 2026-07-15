#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
python <<'PY'
import os
import time

import psycopg2

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
name = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]

for attempt in range(30):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
        )
        conn.close()
        print("PostgreSQL is ready.")
        break
    except psycopg2.OperationalError as exc:
        print(f"  attempt {attempt + 1}/30: {exc}")
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL did not become ready in time.")
PY

python manage.py migrate --noinput
python manage.py seed_demo

exec "$@"
