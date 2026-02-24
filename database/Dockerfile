FROM postgres:16-alpine

# Install required PostgreSQL extensions
RUN apk add --no-cache postgresql-contrib

# Create extensions at startup
COPY ./init-extensions.sql /docker-entrypoint-initdb.d/01-init-extensions.sql

EXPOSE 5432
