# Deployment Guide: Orbital Dynamics Educational Platform

This guide provides comprehensive instructions for deploying the Orbital Dynamics platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Containerization](#docker-containerization)
4. [Cloud Deployment](#cloud-deployment)
   - [AWS EC2](#aws-ec2)
   - [Heroku](#heroku)
   - [DigitalOcean](#digitalocean)
   - [Render](#render)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Security Configuration](#security-configuration)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.8 or higher
- Node.js (optional, for frontend optimization)
- Docker & Docker Compose
- Git
- A domain name (recommended for production)
- SSL/TLS certificate (automated via Let's Encrypt)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/WorkshopApril7To10.git
cd WorkshopApril7To10
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in `backend/` directory:

```env
FLASK_ENV=development
FLASK_DEBUG=True
API_HOST=0.0.0.0
API_PORT=5000
LOG_LEVEL=DEBUG
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 4. Run Development Server

```bash
cd backend
python -m flask run --host 0.0.0.0 --port 5000
```

In another terminal:

```bash
cd frontend/public
# Serve with simple Python server or Use any static server:
python -m http.server 8000
```

Navigate to `http://localhost:8000` in your browser.

---

## Docker Containerization

### 1. Create Dockerfile for Backend

Create `backend/Dockerfile`:

```dockerfile
# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "api.app:app"]
```

### 2. Create Dockerfile for Frontend

Create `frontend/Dockerfile`:

```dockerfile
FROM node:16-alpine as builder

WORKDIR /app

# Copy package files (if using npm build)
# COPY package*.json ./
# RUN npm ci

# Copy frontend files
COPY public/ .

# Build stage (if needed)
# RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy static files
COPY --from=builder /app /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;

    # Gzip compression
    gzip on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript;

    upstream backend {
        server backend:5000;
    }

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # Frontend routes
        location / {
            try_files $uri $uri/ /index.html;
            expires 1h;
            add_header Cache-Control "public, immutable";
        }

        # Static assets  
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # API proxy
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
        }

        # Health check endpoint
        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### 3. Docker Compose Configuration

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./backend/logs:/app/logs

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    environment:
      - API_URL=http://backend:5000/api
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro

  # Optional: PostgreSQL for caching TLE data
  # postgres:
  #   image: postgres:13-alpine
  #   ports:
  #     - "5432:5432"
  #   environment:
  #     - POSTGRES_DB=orbital_dynamics
  #     - POSTGRES_PASSWORD=secure_password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   restart: unless-stopped

volumes:
  postgres_data:

networks:
  default:
    name: orbital_network
```

### 4. Build and Run Locally with Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Cloud Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance

```bash
# 1. Go to AWS Console → EC2 → Launch Instance
# 2. Select Ubuntu 20.04 LTS
# 3. Instance Type: t3.small (free tier) or t3.medium (recommended)
# 4. Configure security group:
#    - Allow SSH (port 22) from your IP
#    - Allow HTTP (port 80) from 0.0.0.0/0
#    - Allow HTTPS (port 443) from 0.0.0.0/0
# 5. Create/select key pair for SSH access
```

#### 2. Connect and Configure Server

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

#### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/WorkshopApril7To10.git
cd WorkshopApril7To10

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### 4. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Update nginx configuration with SSL
# Add to frontend/nginx.conf:
#   listen 443 ssl;
#   ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

# Auto-renewal
sudo certbot renew --dry-run
```

### Heroku Deployment

#### 1. Create Heroku App

```bash
# Install Heroku CLI
# See: https://devcenter.heroku.com/articles/heroku-cli

heroku login
heroku create your-app-name

# Set app name
heroku apps:rename your-new-name
```

#### 2. Configure Procfile

Create `Procfile` in project root:

```
web: cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app
```

#### 3. Create heroku.yml

```yaml
build:
  docker:
    web: backend/Dockerfile
    frontend: frontend/Dockerfile

run:
  web: gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app
```

#### 4. Deploy

```bash
# Deploy from Git
git push heroku main

# View logs
heroku logs --tail

# Scale dynos
heroku ps:scale web=2
```

### DigitalOcean App Platform

#### 1. Connect GitHub Repository

- Go to DigitalOcean → Apps → Create App
- Select GitHub repository
- Connect your GitHub account

#### 2. Configure App Spec

Create `app.yaml` in project root:

```yaml
name: orbital-dynamics
services:
- name: backend
  github:
    branch: main
    deploy_on_push: true
    repo: yourusername/WorkshopApril7To10
  build_command: pip install -r backend/requirements.txt
  source_dir: backend
  http_port: 5000
  envs:
  - key: FLASK_ENV
    value: production
  - key: LOG_LEVEL
    value: INFO

- name: frontend
  github:
    branch: main
    deploy_on_push: true
    repo: yourusername/WorkshopApril7To10
  source_dir: frontend
  http_port: 80
  static_sites:
  - name: frontend_static
    source_dir: /public

domains:
- domain: orbital-dynamics.io
  type: PRIMARY

databases:
- name: tledb
  engine: PG
  version: "12"
```

#### 3. Deploy

```bash
# Push to GitHub
git push origin main

# DigitalOcean automatically deploys
```

### Render Deployment

#### 1. Create New Web Service

- Go to Render → Create → Web Service
- Connect GitHub
- Select repository

#### 2. Configure Service

```
Build Command: pip install -r backend/requirements.txt
Start Command: gunicorn -w 4 -b 0.0.0.0:10000 api.app:app
```

#### 3. Set Environment Variables

```
FLASK_ENV=production
PYTHON_VERSION=3.9
```

---

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Orbital Dynamics

on:
  push:
    branches: [main, production]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest flake8
    
    - name: Lint with flake8
      run: |
        flake8 backend/orbital_mechanics --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Run tests
      run: |
        pytest backend/tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker-compose build
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Push image to Docker Hub
      run: |
        docker tag orbital-dynamics-backend:latest ${{ secrets.DOCKER_USERNAME }}/orbital-dynamics-backend:latest
        docker push ${{ secrets.DOCKER_USERNAME }}/orbital-dynamics-backend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/production' && github.event_name == 'push'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /home/ubuntu/orbital-dynamics
          git pull origin production
          docker-compose pull
          docker-compose up -d
          docker-compose exec backend alembic upgrade head
```

---

## Security Configuration

### 1. Environment Variables

Create `.env.production`:

```env
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
DEBUG=False
LOG_LEVEL=WARNING
CORS_ALLOWED_ORIGINS=https://orbital-dynamics.io,https://www.orbital-dynamics.io
```

### 2. HTTPS/TLS

All traffic should be encrypted:

```nginx
# Enforce HTTPS
server {
    listen 80;
    server_name orbital-dynamics.io;
    return 301 https://$server_name$request_uri;
}
```

### 3. Security Headers

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' cesium.com cdn.jsdelivr.net" always;
```

### 4. Rate Limiting

```python
# In backend/api/app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

@app.route('/api/animation/orbit-frames', methods=['POST'])
@limiter.limit("10 per minute")
def animation_orbit_frames():
    # ...
```

---

## Performance Optimization

### 1. Caching Strategy

```python
# Add to requirements.txt
Flask-Caching==1.10.1
redis==4.0.0

# In backend/api/app.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379'})

@app.route('/api/orbits/list', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour
def list_orbits():
    return jsonify({'orbits': list_all_orbits()})
```

### 2. Database Optimization

```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/orbital_dynamics',
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### 3. CDN Configuration

```nginx
# Use CloudFront for static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
    add_header X-CDN-Cache-Status $upstream_cache_status;
}
```

### 4. Compression

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_proxied any;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
gzip_disable "MSIE [1-6]\.";
```

---

## Monitoring & Logging

### 1. Logging Configuration

```python
# In backend/api/app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Orbital Dynamics API startup')
```

### 2. Health Checks

```bash
# Health check script
#!/bin/bash
curl -f http://localhost/api/health || exit 1
```

### 3. Monitoring Stack (Optional)

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Connection Failed

```bash
# Check if backend is running
docker-compose ps

# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

#### 2. High CPU Usage

```bash
# Check resource usage
docker stats

# Reduce gunicorn workers
# In Dockerfile: CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

#### 3. Out of Memory

```bash
# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew --force-renewal

# Check renewal
sudo certbot certificates
```

#### 5. API Rate Limiting

```bash
# Check rate limits in logs
docker-compose logs backend | grep "429"

# Adjust limits in app.py
limiter.limit("50 per minute")
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.0.x/deployment/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)

---

## Support

For deployment issues or questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review application logs: `docker-compose logs`
3. Check Docker daemon: `systemctl status docker`
4. Verify network connectivity: `curl http://api-host/health`

---

**Last Updated:** January 2024
**Version:** 1.0
**Status:** Production Ready
