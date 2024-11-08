#!/usr/bin/env bash

if [ -f ".env" ]; then
  echo "🌎 .env exists. Leaving alone"
else
  echo "🌎 .env does not exist. Copying .env-example to .env"
  cp env.example .env
  YOUR_UID=$(id -u)
  YOUR_GID=$(id -g)
  echo "🙂 Setting your UID (${YOUR_UID}) and GID (${YOUR_UID}) in .env"
  docker run --rm -v ./.env:/.env alpine echo "$(sed s/YOUR_UID/${YOUR_UID}/ .env)" >.env
  docker run --rm -v ./.env:/.env alpine echo "$(sed s/YOUR_GID/${YOUR_GID}/ .env)" >.env
fi

if [ -f ".config/rclone/rclone.conf" ]; then
  echo "📋 .config/rclone/rclone.conf exists. Leaving alone"
else
  echo "📋 .config/rclone/rclone.conf does not exist. Copying .config/rclone/rclone.conf.example to rclone_config"
  cp .config/rclone/rclone.conf.example .config/rclone/rclone.conf
fi

echo "🚢 Build docker images"
docker compose build

echo "📦 Build python packages"
docker compose run --rm app poetry install

echo "🧳 Run database migrations"
docker compose up -d database
docker compose run --rm app sh -c "cd aim/digifeeds/database && poetry run alembic upgrade heads"

echo "🗄️ Load statuses"
docker compose run --rm app sh -c "poetry run python aim/digifeeds/bin/load_statuses.py"
