# Quick Reference Guide

Quick commands and tips for working with the Medicine Tracker.

---

## Local Development

### Start Development Servers

**Windows:**
```bash
start-local.bat
```

**Linux/Mac:**
```bash
chmod +x start-local.sh
./start-local.sh
```

**Manual Start:**
```bash
# Terminal 1 - Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

### Access Points
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Docker Commands

### Build and Start
```bash
docker-compose up -d --build
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Check Status
```bash
docker-compose ps
```

### Execute Commands in Container
```bash
# Open shell in backend container
docker-compose exec backend /bin/bash

# Run Python command
docker-compose exec backend python -c "print('Hello')"
```

### Remove Everything (Clean Slate)
```bash
docker-compose down -v --remove-orphans
docker system prune -a
```

---

## Database Operations

### Backup Database
```bash
# Local
cp backend/medicine.db backend/medicine_backup_$(date +%Y%m%d).db

# From Docker container
docker-compose exec backend cp medicine.db medicine_backup.db
docker cp medicine-tracker-backend:/app/medicine_backup.db ./
```

### Restore Database
```bash
# Local
cp backend/medicine_backup.db backend/medicine.db

# To Docker container
docker cp medicine_backup.db medicine-tracker-backend:/app/medicine.db
docker-compose restart backend
```

### View Database Contents
```bash
# Install sqlite3 if needed
# On container
docker-compose exec backend sqlite3 medicine.db "SELECT * FROM drugs;"

# Locally
sqlite3 backend/medicine.db "SELECT * FROM drugs;"
```

### Reset Database
```bash
# WARNING: Deletes all data!
rm backend/medicine.db
docker-compose restart backend  # Auto-creates new DB
```

---

## Git Commands

### Initial Setup
```bash
git init
git add .
git commit -m "Initial commit: Medicine Tracker"
git branch -M main
git remote add origin https://github.com/yourusername/medicine-tracker.git
git push -u origin main
```

### Regular Updates
```bash
git add .
git commit -m "Your descriptive message"
git push origin main
```

### Check Status
```bash
git status
git log --oneline -5  # Last 5 commits
```

---

## VPS Commands

### SSH into VPS
```bash
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### Initial Setup on VPS
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install Git
apt install git -y

# Clone repository
git clone https://github.com/yourusername/medicine-tracker.git
cd medicine-tracker

# Create .env file
cp .env.example .env
nano .env  # Edit with your settings

# Start services
docker-compose up -d --build
```

### Update Application on VPS
```bash
cd ~/medicine-tracker
git pull origin main
docker-compose down
docker-compose up -d --build
docker image prune -f  # Clean up old images
```

### Check VPS Status
```bash
# Check running containers
docker-compose ps

# Check system resources
htop  # or top
df -h  # Disk space
free -h  # Memory

# Check logs
docker-compose logs -f
```

---

## Email Testing

### Test Email via API
```bash
curl -X POST http://localhost:8000/test-email
```

### Test Weekly Reminder
```bash
curl -X POST http://localhost:8000/send-weekly-reminder
```

### Test Reorder Reminder
```bash
curl -X POST http://localhost:8000/send-reorder-reminder
```

### Gmail App Password Setup
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password
4. Add to .env file (no spaces)

---

## Common Tasks

### Add a New Drug
1. Open web interface
2. Click "Add New Drug"
3. Fill in all fields
4. Click "Add Drug"

### Refill a Drug
1. Find drug card
2. Click "Refill" button
3. Enter number of packages
4. Click "Refill"

### Edit a Drug
1. Find drug card
2. Click "Edit" button
3. Modify fields
4. Click "Update Drug"

### Delete a Drug
1. Find drug card
2. Click "Delete" button
3. Confirm deletion

---

## API Usage (cURL Examples)

### Get All Drugs
```bash
curl http://localhost:8000/drugs/
```

### Get Single Drug
```bash
curl http://localhost:8000/drugs/1
```

### Create Drug
```bash
curl -X POST http://localhost:8000/drugs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aspirin",
    "package_size": 30,
    "pills_per_dose": 1,
    "times_per_day": 2,
    "current_amount": 60,
    "is_quarterly": false
  }'
```

### Update Drug
```bash
curl -X PUT http://localhost:8000/drugs/1 \
  -H "Content-Type: application/json" \
  -d '{
    "current_amount": 90
  }'
```

### Refill Drug
```bash
curl -X POST http://localhost:8000/drugs/1/refill \
  -H "Content-Type: application/json" \
  -d '{
    "packages": 2
  }'
```

### Delete Drug
```bash
curl -X DELETE http://localhost:8000/drugs/1
```

### Get Drugs Needing Reorder
```bash
curl http://localhost:8000/drugs-status/reorder
```

---

## Nginx Configuration

### Install Nginx
```bash
apt install nginx -y
```

### Create Config File
```bash
nano /etc/nginx/sites-available/medicine-tracker
```

### Basic Config (HTTP)
```nginx
server {
    listen 80;
    server_name medicine.yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enable Site
```bash
ln -s /etc/nginx/sites-available/medicine-tracker /etc/nginx/sites-enabled/
nginx -t  # Test configuration
systemctl reload nginx
```

### Add SSL (HTTPS)
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d medicine.yourdomain.com

# Auto-renewal is set up automatically
certbot renew --dry-run  # Test renewal
```

---

## Monitoring

### Check Service Health
```bash
# API health check
curl http://localhost:8000/

# Full status
curl http://localhost:8000/docs
```

### Monitor Logs in Real-Time
```bash
# All logs
docker-compose logs -f

# Filter for errors
docker-compose logs -f | grep -i error

# Backend only
docker-compose logs -f backend
```

### System Monitoring
```bash
# CPU and Memory
docker stats

# Disk usage
docker system df

# Container inspect
docker inspect medicine-tracker-backend
```

---

## Troubleshooting Quick Fixes

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Frontend Won't Load
```bash
# Check logs
docker-compose logs frontend

# Rebuild
docker-compose down
docker-compose up -d --build

# Clear browser cache
```

### Email Not Sending
```bash
# Check environment variables
docker-compose exec backend env | grep SMTP

# Test connectivity
telnet smtp.gmail.com 587

# Check logs
docker-compose logs backend | grep -i email
```

### Database Locked
```bash
# Stop all containers
docker-compose down

# Start again
docker-compose up -d
```

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in docker-compose.yml
```

---

## Environment Variables

### Required Variables (.env)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com
```

### Check Current Values
```bash
# In container
docker-compose exec backend env | grep SMTP

# Locally
cat backend/.env
```

---

## Scheduled Tasks

### View Current Schedule
Check `backend/app/main.py`:
- Weekly reminder: Sunday 9:00 AM
- Reorder check: Daily 10:00 AM

### Modify Schedule
Edit `backend/app/main.py`:

```python
# Change to Saturday 8:00 AM
scheduler.add_job(
    send_weekly_reminder_job,
    CronTrigger(day_of_week="sat", hour=8, minute=0),
    id="weekly_reminder",
)
```

Then restart:
```bash
docker-compose restart backend
```

### Trigger Manually (via UI)
1. Open web interface
2. Click "Send Weekly Reminder" or "Send Reorder Reminder"

---

## Performance Tips

### Speed Up Docker Builds
```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker-compose build

# Prune build cache occasionally
docker builder prune
```

### Optimize Frontend
```bash
# Production build
cd frontend
npm run build

# Check bundle size
ls -lh dist/assets/
```

### Database Optimization
```bash
# Add indexes (edit models.py)
# Then recreate database or use migrations
```

---

## Backup Strategy

### Automated Backup Script
Create `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker cp medicine-tracker-backend:/app/medicine.db ./backups/medicine_$DATE.db
# Keep only last 7 days
find ./backups -name "medicine_*.db" -mtime +7 -delete
```

Run daily with cron:
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## Useful Aliases

Add to `.bashrc` or `.zshrc`:

```bash
# Navigate to project
alias med='cd ~/medicine-tracker'

# View logs
alias medlogs='docker-compose logs -f'

# Restart services
alias medrestart='docker-compose restart'

# Update and deploy
alias medupdate='git pull origin main && docker-compose down && docker-compose up -d --build'
```

---

## Support Links

- FastAPI Docs: https://fastapi.tiangolo.com
- Svelte Docs: https://svelte.dev
- Docker Docs: https://docs.docker.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Nginx Docs: https://nginx.org/en/docs/

---

## Quick Checklist

### Before First Use
- [ ] Install Python 3.11+
- [ ] Install Node.js 20+
- [ ] Install Docker & Docker Compose
- [ ] Configure email settings in .env
- [ ] Test email functionality
- [ ] Add initial drug data

### Before Deployment
- [ ] Update .env with production values
- [ ] Set up VPS
- [ ] Configure domain DNS
- [ ] Set up GitHub repository
- [ ] Configure GitHub secrets
- [ ] Set up SSL certificate
- [ ] Test deployment
- [ ] Set up backups

### Regular Maintenance
- [ ] Check logs weekly
- [ ] Backup database daily
- [ ] Update system packages monthly
- [ ] Review email reminders
- [ ] Check disk space
- [ ] Verify SSL certificate renewal

---

**Keep this file handy for quick reference!** 📋
