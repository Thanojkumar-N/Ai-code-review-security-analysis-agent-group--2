# Stage 1: Build React Application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json files
COPY package.json ./
COPY frontend/package.json ./frontend/

# Install packages
RUN npm install --workspace=frontend

# Copy frontend source files
COPY frontend/ ./frontend/

# Build application
RUN npm run build --workspace=frontend

# Stage 2: Serve React application via Nginx
FROM nginx:1.25-alpine

# Copy built frontend assets to Nginx html directory
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
