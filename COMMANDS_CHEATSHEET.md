# 🚀 Commands Cheatsheet - AI Virtual World

Quick reference for all commands and shortcuts.

---

## 📦 Installation

### First Time Setup
```bash
# Clone repository (if from git)
git clone <repository-url>
cd AI

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Quick Install (All at once)
```bash
npm run install:all
```

---

## ▶️ Starting Services

### Option 1: One-Click Start (Windows)
```bash
start-all.bat
```

### Option 2: Manual Start

#### Backend Only
```bash
python -m uvicorn api.main:app --reload --port 8000
```

#### Frontend Only
```bash
cd frontend
npm start
```

#### Both Services (with npm)
```bash
npm start
```

---

## 🎮 Training Commands

### Basic Training
```bash
# Headless training (no visualization)
python main.py --mode train --episodes 100

# Visual training (with Pygame)
python main.py --mode visual --episodes 50

# Compare algorithms
python main.py --mode compare --episodes 100
```

### Advanced Training
```bash
# Custom number of agents
python main.py --mode train --episodes 200 --agents 8

# Specific algorithm
python main.py --mode train --episodes 100 --algorithm dqn

# With custom learning rate
python main.py --mode train --episodes 100 --lr 0.001
```

### NPM Scripts
```bash
npm run train              # 100 episodes headless
npm run train:visual       # 50 episodes with visualization
npm run train:compare      # Compare algorithms
```

---

## 🌐 Web Dashboard

### Flask Dashboard (Legacy)
```bash
python main.py --mode dashboard
# Access: http://localhost:5000
```

### Angular Dashboard (New)
```bash
cd frontend
npm start
# Access: http://localhost:4200
```

---

## 🧪 Testing

### Test Backend API
```bash
python test_api.py
```

### Test Frontend
```bash
cd frontend
npm test
```

### Run All Tests
```bash
npm run test:backend
npm run test:frontend
```

---

## 🔍 Development

### Backend Development
```bash
# Run with auto-reload
python -m uvicorn api.main:app --reload

# Run on different port
python -m uvicorn api.main:app --port 8001

# Run with multiple workers (production)
python -m uvicorn api.main:app --workers 4
```

### Frontend Development
```bash
cd frontend

# Development server
npm start

# Build for production
npm run build

# Watch mode
npm run watch

# Lint code
npm run lint
ng lint
```

---

## 📊 API Endpoints

### Health & Status
```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs
```

### Training
```bash
# Get training status
curl http://localhost:8000/api/training/status

# Start training
curl -X POST http://localhost:8000/api/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "dqn",
    "episodes": 100,
    "learning_rate": 0.001,
    "gamma": 0.99,
    "epsilon": 0.1
  }'

# Stop training
curl -X POST http://localhost:8000/api/training/stop/{session_id}

# Get training history
curl http://localhost:8000/api/training/history
```

### Models
```bash
# Get all models
curl http://localhost:8000/api/models

# Delete model
curl -X DELETE http://localhost:8000/api/models/{model_name}
```

### Statistics
```bash
# Get summary
curl http://localhost:8000/api/stats/summary

# Get performance stats
curl http://localhost:8000/api/stats/performance
```

### Algorithms
```bash
# Get available algorithms
curl http://localhost:8000/api/algorithms
```

---

## 🗂️ File Management

### Clean Project
```bash
# Clean all generated files
npm run clean

# Clean frontend only
cd frontend
rm -rf node_modules dist
npm install

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Backup Data
```bash
# Backup models
cp -r models models_backup_$(date +%Y%m%d)

# Backup logs
cp -r logs logs_backup_$(date +%Y%m%d)

# Backup configs
cp config/settings.yaml config/settings_backup_$(date +%Y%m%d).yaml
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Create .env file
cp .env.example .env

# Edit .env
nano .env
```

### Settings
```bash
# Edit YAML config
nano config/settings.yaml

# Edit frontend environment
nano frontend/src/environments/environment.ts
```

---

## 📝 Logging

### View Logs
```bash
# View latest training log
tail -f logs/training_*.jsonl

# View all logs
ls -lh logs/

# Count episodes in log
wc -l logs/training_*.jsonl
```

### Analyze Logs
```bash
# Extract rewards
cat logs/training_*.jsonl | jq '.reward'

# Calculate average reward
cat logs/training_*.jsonl | jq '.reward' | awk '{sum+=$1} END {print sum/NR}'

# Find best episode
cat logs/training_*.jsonl | jq -s 'max_by(.reward)'
```

---

## 🎨 Frontend Commands

### Angular CLI
```bash
cd frontend

# Generate component
ng generate component components/my-component

# Generate service
ng generate service services/my-service

# Generate module
ng generate module modules/my-module

# Serve with specific configuration
ng serve --configuration production

# Build with optimization
ng build --prod --optimization
```

### Package Management
```bash
# Install package
npm install <package-name>

# Install dev dependency
npm install --save-dev <package-name>

# Update packages
npm update

# Check outdated packages
npm outdated

# Audit security
npm audit
npm audit fix
```

---

## 🐛 Debugging

### Backend Debugging
```bash
# Run with debug mode
python -m pdb main.py

# Check Python environment
python -c "import sys; print(sys.version)"
python -c "import torch; print(torch.__version__)"

# Test imports
python -c "from api.main import app; print('OK')"
```

### Frontend Debugging
```bash
cd frontend

# Check Angular version
ng version

# Check Node/NPM versions
node --version
npm --version

# Clear Angular cache
ng cache clean

# Rebuild node_modules
rm -rf node_modules package-lock.json
npm install
```

### Network Debugging
```bash
# Check if port is in use
netstat -ano | findstr :8000
netstat -ano | findstr :4200

# Kill process on port (Windows)
taskkill /PID <PID> /F

# Test API connection
curl -v http://localhost:8000/api/health

# Test WebSocket
wscat -c ws://localhost:8000/ws/training
```

---

## 📦 Build & Deploy

### Frontend Build
```bash
cd frontend

# Development build
ng build

# Production build
ng build --configuration production

# Build with base href
ng build --base-href /ai-dashboard/

# Analyze bundle size
ng build --stats-json
npx webpack-bundle-analyzer dist/stats.json
```

### Backend Build
```bash
# Create requirements.txt
pip freeze > requirements.txt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install in virtual environment
pip install -r requirements.txt
```

---

## 🚀 Production Deployment

### Backend (Uvicorn)
```bash
# Production server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# With SSL
uvicorn api.main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem

# Behind reverse proxy
uvicorn api.main:app --proxy-headers --forwarded-allow-ips='*'
```

### Frontend (Nginx)
```bash
# Build production
cd frontend
ng build --configuration production

# Copy to nginx
cp -r dist/* /var/www/html/

# Restart nginx
sudo systemctl restart nginx
```

---

## 🔐 Security

### Generate Secrets
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate UUID
python -c "import uuid; print(uuid.uuid4())"
```

### SSL Certificates
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

---

## 📊 Performance Monitoring

### Backend Performance
```bash
# Profile Python code
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats

# Memory profiling
python -m memory_profiler main.py

# Monitor CPU/Memory
top -p $(pgrep -f uvicorn)
```

### Frontend Performance
```bash
cd frontend

# Lighthouse audit
npm install -g lighthouse
lighthouse http://localhost:4200

# Bundle analysis
ng build --stats-json
npx webpack-bundle-analyzer dist/stats.json
```

---

## 🎯 Quick Actions

### Daily Development
```bash
# Start everything
start-all.bat

# Test API
python test_api.py

# View logs
tail -f logs/training_*.jsonl

# Check status
curl http://localhost:8000/api/health
```

### Before Commit
```bash
# Format code
npm run format

# Lint
npm run lint:frontend

# Test
npm run test:backend
npm run test:frontend

# Build
npm run build:frontend
```

### Troubleshooting
```bash
# Restart services
taskkill /F /IM python.exe
taskkill /F /IM node.exe
start-all.bat

# Clear cache
npm run clean
pip cache purge

# Reinstall
npm run install:all
```

---

## 📚 Documentation

### Generate Docs
```bash
# Backend API docs (automatic)
# Access: http://localhost:8000/docs

# Frontend docs (TypeDoc)
cd frontend
npm install --save-dev typedoc
npx typedoc --out docs src/
```

### View Docs
```bash
# API documentation
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc

# Frontend docs
open frontend/docs/index.html
```

---

## 💡 Tips & Tricks

### Aliases (Add to .bashrc or .zshrc)
```bash
alias ai-start="cd ~/AI && start-all.bat"
alias ai-test="cd ~/AI && python test_api.py"
alias ai-logs="cd ~/AI && tail -f logs/training_*.jsonl"
alias ai-clean="cd ~/AI && npm run clean"
```

### Git Shortcuts
```bash
alias gs="git status"
alias ga="git add ."
alias gc="git commit -m"
alias gp="git push"
alias gl="git log --oneline --graph"
```

---

## 🆘 Emergency Commands

### Kill All Processes
```bash
# Windows
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Linux/Mac
pkill -f uvicorn
pkill -f "ng serve"
```

### Reset Everything
```bash
# Full reset
npm run clean
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### Backup Before Reset
```bash
# Quick backup
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz models/ logs/ config/
```

---

**Last Updated:** May 10, 2026
**Version:** 2.0.0

**Pro Tip:** Bookmark this file for quick reference! 🔖
