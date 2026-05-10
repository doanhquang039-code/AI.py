# 🚀 Deployment Guide - AI Virtual World

## Quick Deploy (3 Steps)

### Step 1: Install
```bash
npm run install:all
```

### Step 2: Start
```bash
start-all.bat
```

### Step 3: Access
- Frontend: http://localhost:4200
- API: http://localhost:8000/docs

---

## Production Deployment

### Backend (Uvicorn)
```bash
# Production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# With SSL
uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem
```

### Frontend (Build)
```bash
cd frontend
ng build --configuration production
```

### Docker (Optional)
```bash
# Build image
docker build -t ai-virtual-world .

# Run container
docker run -p 8000:8000 -p 4200:4200 ai-virtual-world
```

---

## Environment Variables

Create `.env` file:
```env
# Backend
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Frontend
FRONTEND_PORT=4200
API_URL=http://localhost:8000

# Training
MAX_EPISODES=1000
NUM_AGENTS=4
```

---

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/ai-virtual-world/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Systemd Service

Create `/etc/systemd/system/ai-backend.service`:
```ini
[Unit]
Description=AI Virtual World Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ai-virtual-world
Environment="PATH=/var/www/ai-virtual-world/venv/bin"
ExecStart=/var/www/ai-virtual-world/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-backend
sudo systemctl start ai-backend
sudo systemctl status ai-backend
```

---

## Health Checks

### Backend
```bash
curl http://localhost:8000/api/health
```

### Frontend
```bash
curl http://localhost:4200
```

---

## Monitoring

### Logs
```bash
# Backend logs
tail -f logs/training_*.jsonl

# System logs
journalctl -u ai-backend -f
```

### Performance
```bash
# CPU & Memory
top -p $(pgrep -f uvicorn)

# Network
netstat -tulpn | grep :8000
```

---

## Backup

### Automated Backup Script
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/ai-virtual-world"

# Create backup
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
  models/ \
  logs/ \
  config/

# Keep only last 7 days
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete
```

---

## Security

### SSL Certificate (Let's Encrypt)
```bash
sudo certbot --nginx -d your-domain.com
```

### Firewall
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow API port (if needed)
sudo ufw allow 8000/tcp
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version

# Check dependencies
pip list

# Check port
netstat -tulpn | grep :8000
```

### Frontend won't build
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version
```

---

## Scaling

### Horizontal Scaling
```bash
# Multiple backend workers
uvicorn api.main:app --workers 8

# Load balancer (Nginx)
upstream backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Vertical Scaling
- Increase worker count
- Allocate more RAM
- Use GPU for training

---

## CI/CD

### GitHub Actions
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          ssh user@server 'cd /var/www/ai-virtual-world && git pull && npm run install:all && systemctl restart ai-backend'
```

---

## Status: ✅ Ready for Production

**Last Updated:** May 10, 2026  
**Version:** 2.0.0
