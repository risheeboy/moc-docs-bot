FROM nginx:1.25-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Copy main nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy route configs
COPY conf.d/ /etc/nginx/conf.d/

# Create self-signed certificate (will be overridden in production)
RUN apk add --no-cache openssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=IN/ST=Delhi/L=Delhi/O=Ministry of Culture/CN=culture.gov.in" && \
    apk del openssl

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
