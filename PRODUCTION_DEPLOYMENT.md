# Khanal Tech Integrations - Production Deployment Guide

## Overview
This project contains two Vue.js applications running on the same Frappe site:
1. **Frontend** (`/home`) - Main CRM/ERP interface
2. **Kiosk Frontend** (`/kiosk`) - Production kiosk interface

## Architecture
- **Backend**: Frappe Framework (Python)
- **Frontend**: Vue.js 3 + Vite
- **Database**: MariaDB/MySQL
- **Cache**: Redis
- **Web Server**: Nginx (production) / Werkzeug (development)

## Production Deployment

### 1. Environment Setup
```bash
# Install system dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
sudo apt install mariadb-server redis-server nginx
sudo apt install nodejs npm yarn

# Create production user
sudo useradd -m -s /bin/bash frappe
sudo su - frappe
```

### 2. Frappe Bench Setup
```bash
# Install bench
pip3.12 install frappe-bench

# Create production bench
bench init --python python3.12 production-bench
cd production-bench

# Create site
bench new-site your-domain.com --admin-password your-admin-password

# Install apps
bench get-app khanal_tech_integrations
bench install-app khanal_tech_integrations
```

### 3. Build Assets
```bash
# Build both Vue.js applications
cd apps/khanal_tech_integrations
yarn install
yarn build

cd ../kiosk-frontend
yarn install
yarn build

# Build Frappe assets
cd ../../
bench build
```

### 4. Production Configuration

#### Nginx Configuration
Create `/etc/nginx/sites-available/khanal-tech`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Static files
    location /assets/ {
        alias /home/frappe/production-bench/sites/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Kiosk static files
    location /kiosk/assets/ {
        alias /home/frappe/production-bench/apps/khanal_tech_integrations/khanal_tech_integrations/www/kiosk/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Systemd Service
Create `/etc/systemd/system/frappe.service`:
```ini
[Unit]
Description=Frappe Production Server
After=network.target

[Service]
Type=simple
User=frappe
Group=frappe
WorkingDirectory=/home/frappe/production-bench
ExecStart=/home/frappe/production-bench/env/bin/python -m frappe serve --port 8000 --host 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Environment Variables
Create `/home/frappe/production-bench/sites/your-domain.com/site_config.json`:
```json
{
    "db_host": "localhost",
    "db_port": 3306,
    "db_name": "your_database_name",
    "db_password": "your_database_password",
    "redis_cache": "redis://localhost:13000",
    "redis_queue": "redis://localhost:11000",
    "redis_socketio": "redis://localhost:12000",
    "scheduler_enabled": 1,
    "developer_mode": 0,
    "maintenance_mode": 0
}
```

### 6. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Start Services
```bash
# Enable and start services
sudo systemctl enable nginx
sudo systemctl enable frappe
sudo systemctl enable redis-server
sudo systemctl enable mariadb

sudo systemctl start nginx
sudo systemctl start frappe
sudo systemctl start redis-server
sudo systemctl start mariadb

# Start Frappe workers
cd /home/frappe/production-bench
bench start
```

## Development vs Production

### Development
- **URL**: `http://kfltest.localhost:8003`
- **Kiosk**: `http://kfltest.localhost:8003/kiosk`
- **Main App**: `http://kfltest.localhost:8003/`

### Production
- **URL**: `https://your-domain.com`
- **Kiosk**: `https://your-domain.com/kiosk`
- **Main App**: `https://your-domain.com/`

## Key Features

### Dynamic Configuration
- No hardcoded URLs or ports
- Automatic site detection
- Environment-aware API endpoints
- Production/development mode detection

### Both Apps on Same Site
- **Frontend**: Serves the main CRM/ERP interface
- **Kiosk Frontend**: Serves the production kiosk interface
- Shared authentication and session management
- Unified API endpoints

### Production Ready
- SSL/HTTPS support
- Proper caching headers
- Security headers
- WebSocket support
- Service management
- Auto-renewal certificates

## Monitoring

### Logs
```bash
# Application logs
tail -f /home/frappe/production-bench/logs/web.log
tail -f /home/frappe/production-bench/logs/worker.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u frappe -f
```

### Health Checks
```bash
# Check services
sudo systemctl status nginx frappe redis-server mariadb

# Check site
curl -I https://your-domain.com
curl -I https://your-domain.com/kiosk
```

## Backup Strategy
```bash
# Database backup
bench --site your-domain.com backup

# File backup
tar -czf backup-$(date +%Y%m%d).tar.gz /home/frappe/production-bench/sites/your-domain.com
```

## Updates
```bash
# Update Frappe
bench update

# Update apps
bench --site your-domain.com migrate

# Rebuild assets
bench build
```

This setup ensures both Vue.js applications work seamlessly on the same Frappe site without hardcoded configurations and is ready for production deployment.
