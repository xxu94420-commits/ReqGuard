FROM maven:3.9.11-eclipse-temurin-17 AS java-build
WORKDIR /build
COPY backend/pom.xml ./
COPY backend/src ./src
RUN mvn -B -ntp verify

FROM node:24-alpine AS web-build
WORKDIR /build
RUN npm install -g pnpm@11.19.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless nginx openssl && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY ai-service/pyproject.toml /srv/ai-service/
RUN python3 -m venv /srv/venv && /srv/venv/bin/pip install --no-cache-dir /srv/ai-service
COPY ai-service/app /srv/ai-service/app
COPY dataset /srv/dataset
COPY --from=java-build /build/target/reqguard-0.1.0.jar /srv/app.jar
COPY --from=web-build /build/dist /srv/web
COPY deploy/render/start.py deploy/render/auth.py deploy/render/nginx.conf /srv/deploy/
RUN useradd --uid 10001 --create-home reqguard && mkdir /srv/data && chown -R reqguard:reqguard /srv/data
USER reqguard
ENV PORT=10000 PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["/srv/venv/bin/python", "/srv/deploy/start.py"]
