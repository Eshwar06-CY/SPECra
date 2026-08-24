# ==============================================================================
# SPECra Frontend Production Dockerfile
# Multi-Stage Build: Node.js Build -> Nginx Alpine
# ==============================================================================

# --- Stage 1: Build Stage ---
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build production bundle
COPY . .
RUN npm run build

# --- Stage 2: Runtime Stage ---
FROM nginx:1.25-alpine as runtime

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
