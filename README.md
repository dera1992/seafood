# Seafood

Seafood is a Django-based marketplace application with multi-role users (customers, shop owners, dispatchers) and shop management, ordering, chat, and marketing features. It supports geocoding and PostGIS for shop locations, and can be run locally with Docker and a PostGIS-enabled PostgreSQL database.

## Tech Stack

- **Backend:** Django 4.2
- **Database:** PostgreSQL + PostGIS (recommended), SQLite fallback for local dev
- **Frontend:** Server-rendered templates with static assets
- **Auth:** Email-based custom user model with social auth
- **Geo:** GeoDjango + PostGIS

## Project Structure

- `account/` – users, profiles, shops, subscriptions
- `foodCreate/` – products and categories
- `cart/`, `order/` – shopping and checkout
- `chat/` – shop/customer messaging
- `templates/`, `static/` – UI and assets
- `seafood/` – Django project settings and URLs

## Requirements

- Python 3.11+
- PostGIS-enabled PostgreSQL (if using spatial features)
- Docker + Docker Compose (recommended for local setup)

## Environment Variables

Create a `.env` file (or copy from `.env.example`) in the project root:

```bash
cp .env.example .env
```

Key variables:

- `DEBUG`: Django debug flag (`1` or `0`)
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of hosts
- `DATABASE_URL`: Database connection string
- `DATABASE_ENGINE`: Django DB engine (use PostGIS engine for spatial)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Postgres credentials

## Run with Docker (PostGIS)

This is the recommended development workflow.

```bash
docker compose up --build
```

The app will be available at `http://localhost:8000` and will auto-run migrations on startup.

If port `5432` is already in use on your machine, set `POSTGRES_PORT` in your `.env` file (for example `POSTGRES_PORT=5433`) before starting Docker.

### Troubleshooting Docker startup

If `docker compose ps -a` shows containers in **Created** state and there are no logs, the containers were created but never started. From the project root, run:

```bash
docker compose up --build
```

If they still remain in **Created**, try restarting them explicitly:

```bash
docker compose start
```

You can also remove the stopped containers and recreate them:

```bash
docker compose rm -f
docker compose up --build
```

If none of the above starts the containers, check Docker Desktop/daemon status and ensure you are running the commands from the folder that contains `docker-compose.yml`.

### Notes on PostGIS

The container uses the `postgis/postgis` image and the Django config defaults to:

```
DATABASE_ENGINE=django.contrib.gis.db.backends.postgis
```

This enables GeoDjango features like `PointField` for shop locations.

## Run Locally (Without Docker)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure your `.env` (or set environment variables).

3. Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

If you do not set `DATABASE_URL`, the project falls back to SQLite.

## Geolocation / Shop Location

Shop locations are stored in a single PostGIS `PointField` (`account.Shop.location`). If a shop has no location, the save hook attempts to geocode using the address fields and populate a `Point` (SRID 4326).

## Common Commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Testing

Run Django tests with:

```bash
python manage.py test
```

## License

This project currently does not include a license file. Add one if needed.
