# Production Deployment Guide for WebGST

This guide covers deploying WebGST to a production Linux server (Ubuntu/Debian).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Web Server Configuration](#web-server-configuration)
6. [SSL/HTTPS Setup](#sslhttps-setup)
7. [Systemd Service](#systemd-service)
8. [Firewall Configuration](#firewall-configuration)
9. [Automated Backups](#automated-backups)
10. [Monitoring](#monitoring)

---

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root or sudo access
- Domain name pointed to server IP
- At least 2GB RAM, 20GB disk space

---

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python 3.11+

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### 3. Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
```

### 4. Install Nginx

```bash
sudo apt install -y nginx
```

### 5. Install Let's Encrypt Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## Database Setup

### 1. Create Database User

```bash
sudo -u postgres psql
```

```sql
CREATE USER webgst_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE webgst_db OWNER webgst_user;
GRANT ALL PRIVILEGES ON DATABASE webgst_db TO webgst_user;
\q
```

### 2. Configure PostgreSQL for Local Access

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# Add this line
local   webgst_db       webgst_user                             md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 3. Test Connection

```bash
psql -U webgst_user -d webgst_db -h localhost
# Enter password when prompted
```

---

## Application Deployment

### 1. Create Application User

```bash
sudo useradd -m -s /bin/bash webgst
sudo usermod -aG sudo webgst  # Optional: if user needs sudo
```

### 2. Clone Repository

```bash
sudo mkdir -p /var/www/webgst
sudo chown webgst:webgst /var/www/webgst
sudo -u webgst git clone https://github.com/yourusername/webgst.git /var/www/webgst
cd /var/www/webgst
```

### 3. Setup Backend

```bash
cd /var/www/webgst/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]
```

### 4. Configure Environment

```bash
# Copy production template
cp .env.production .env

# Edit configuration
nano .env
```

Update these critical values:

```env
DATABASE_URL=postgresql://webgst_user:your_secure_password@localhost:5432/webgst_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DEBUG=False
ADMIN_REGISTRATION_ENABLED=False
ALLOWED_ORIGINS=https://your-domain.com
```

### 5. Run Database Migrations

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run migrations (if using Alembic)
alembic upgrade head

# Or initialize database directly
python -c "from app.database import init_db; init_db()"
```

### 6. Create First Admin User

```bash
python -c "
from app.models.user import User
from app.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

admin = User(
    email='admin@your-domain.com',
    hashed_password=pwd_context.hash('CHANGE_THIS_PASSWORD'),
    full_name='Admin User',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

**IMPORTANT**: Change password immediately after first login!

### 7. Setup Frontend

```bash
# Copy frontend files
sudo mkdir -p /var/www/webgst/frontend
sudo cp -r /var/www/webgst/frontend/* /var/www/webgst/frontend/

# Set permissions
sudo chown -R www-data:www-data /var/www/webgst/frontend
sudo chmod -R 755 /var/www/webgst/frontend
```

---

## Web Server Configuration

### Option A: Nginx (Recommended)

```bash
# Copy nginx configuration
sudo cp /var/www/webgst/backend/nginx.conf /etc/nginx/sites-available/webgst

# Update configuration
sudo nano /etc/nginx/sites-available/webgst
# Change: your-domain.com to your actual domain
# Change: /var/www/webgst paths if different

# Enable site
sudo ln -s /etc/nginx/sites-available/webgst /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Option B: Caddy (Alternative)

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Copy Caddyfile
sudo cp /var/www/webgst/backend/Caddyfile /etc/caddy/Caddyfile

# Update domain
sudo nano /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

---

## SSL/HTTPS Setup

### Using Certbot (Nginx)

```bash
# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts, choose redirect HTTP to HTTPS
```

### Using Caddy

Caddy automatically obtains and renews SSL certificates from Let's Encrypt. No manual setup required!

### Test Auto-Renewal

```bash
# Nginx
sudo certbot renew --dry-run

# Certbot auto-renewal is configured via systemd timer
sudo systemctl status certbot.timer
```

---

## Systemd Service

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/webgst.service
```

Add this content:

```ini
[Unit]
Description=WebGST FastAPI Application
After=network.target postgresql.service

[Service]
Type=notify
User=webgst
Group=webgst
WorkingDirectory=/var/www/webgst/backend
Environment="PATH=/var/www/webgst/backend/venv/bin"
ExecStart=/var/www/webgst/backend/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/webgst/access.log \
    --error-logfile /var/log/webgst/error.log \
    --log-level info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/webgst
sudo chown webgst:webgst /var/log/webgst
```

### 3. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable webgst

# Start service
sudo systemctl start webgst

# Check status
sudo systemctl status webgst

# View logs
sudo journalctl -u webgst -f
```

### 4. Service Management Commands

```bash
# Start
sudo systemctl start webgst

# Stop
sudo systemctl stop webgst

# Restart
sudo systemctl restart webgst

# Reload (graceful restart)
sudo systemctl reload webgst

# View logs
sudo journalctl -u webgst -n 100 -f
```

---

## Firewall Configuration

### Using UFW (Ubuntu)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (only if remote access needed)
# sudo ufw allow 5432/tcp

# Check status
sudo ufw status verbose

# Check active connections
sudo ufw status numbered
```

### Using iptables (Alternative)

```bash
# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Drop all other input
sudo iptables -P INPUT DROP

# Save rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## Automated Backups

### 1. Copy Backup Scripts

```bash
sudo mkdir -p /opt/webgst/scripts
sudo cp /var/www/webgst/backend/backup.ps1 /opt/webgst/scripts/backup.sh
sudo chmod +x /opt/webgst/scripts/backup.sh
```

### 2. Convert PowerShell Script to Bash

Create `/opt/webgst/scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/webgst"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
DB_USER="webgst_user"
DB_NAME="webgst_db"

# Create backup directory
mkdir -p "$BACKUP_PATH"

echo "========================================="
echo "  WebGST Backup - $TIMESTAMP"
echo "========================================="

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
export PGPASSWORD="your_secure_password"
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_PATH/webgst_pg.dump"
echo "✓ PostgreSQL backup complete"

# Backup .env file
echo "Backing up configuration..."
cp /var/www/webgst/backend/.env "$BACKUP_PATH/.env"
echo "✓ Configuration backup complete"

# Backup uploads (if any)
if [ -d "/var/www/webgst/backend/uploads" ]; then
    cp -r /var/www/webgst/backend/uploads "$BACKUP_PATH/uploads"
fi

# Compress backup
echo "Compressing backup..."
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "backup_$TIMESTAMP"
rm -rf "$BACKUP_PATH"
echo "✓ Backup compressed"

# Delete old backups (keep last 30 days)
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete
echo "✓ Old backups cleaned"

echo ""
echo "========================================="
echo "Backup completed successfully!"
echo "Location: $BACKUP_PATH.tar.gz"
echo "Size: $(du -h "$BACKUP_PATH.tar.gz" | cut -f1)"
echo "========================================="
```

### 3. Setup Cron Job

```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/webgst/scripts/backup.sh >> /var/log/webgst/backup.log 2>&1

# Or weekly on Sunday at 3 AM
0 3 * * 0 /opt/webgst/scripts/backup.sh >> /var/log/webgst/backup.log 2>&1
```

---

## Monitoring

### 1. Application Health Check

```bash
# Check if service is running
sudo systemctl status webgst

# Test API endpoint
curl http://localhost:8000/health

# Check logs
sudo tail -f /var/log/webgst/access.log
sudo tail -f /var/log/webgst/error.log
```

### 2. Database Monitoring

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Monitor connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='webgst_db';"

# Check database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('webgst_db'));"
```

### 3. Server Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Network connections
sudo netstat -tulpn | grep LISTEN
```

### 4. Setup Monitoring Tools (Optional)

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Install fail2ban for security
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
```

---

## Post-Deployment Checklist

- [ ] Database is backed up
- [ ] .env file has production values
- [ ] SECRET_KEY is unique and secure (not default)
- [ ] DEBUG=False
- [ ] ADMIN_REGISTRATION_ENABLED=False
- [ ] SSL certificate is installed and auto-renewing
- [ ] Firewall is configured (ports 80, 443, 22 only)
- [ ] Systemd service is enabled and running
- [ ] Nginx/Caddy is configured with security headers
- [ ] Automated backups are scheduled
- [ ] Log rotation is configured
- [ ] First admin user is created
- [ ] Test invoice generation works
- [ ] Test PDF export works
- [ ] Test GST calculations are correct
- [ ] Monitor logs for 24 hours after deployment

---

## Troubleshooting

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u webgst -n 50 --no-pager

# Check permissions
ls -la /var/www/webgst/backend

# Test manually
cd /var/www/webgst/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Database Connection Error

```bash
# Test PostgreSQL connection
psql -U webgst_user -d webgst_db -h localhost

# Check DATABASE_URL in .env
cat /var/www/webgst/backend/.env | grep DATABASE_URL

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 502 Bad Gateway (Nginx)

```bash
# Check if backend service is running
sudo systemctl status webgst

# Check nginx error logs
sudo tail -f /var/log/nginx/webgst_error.log

# Test backend directly
curl http://127.0.0.1:8000/health
```

### SSL Certificate Issues

```bash
# Test SSL renewal
sudo certbot renew --dry-run

# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

---

## Maintenance

### Update Application

```bash
cd /var/www/webgst
sudo -u webgst git pull

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head

# Restart service
sudo systemctl restart webgst
```

### Database Maintenance

```bash
# Vacuum database
sudo -u postgres psql -d webgst_db -c "VACUUM ANALYZE;"

# Check for bloat
sudo -u postgres psql -d webgst_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Log Rotation

Create `/etc/logrotate.d/webgst`:

```
/var/log/webgst/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 webgst webgst
    sharedscripts
    postrotate
        systemctl reload webgst > /dev/null 2>&1 || true
    endscript
}
```

---

## Security Best Practices

1. **Keep system updated**: `sudo apt update && sudo apt upgrade -y`
2. **Use strong passwords**: For database, admin accounts
3. **Restrict SSH**: Disable password auth, use SSH keys only
4. **Enable fail2ban**: Protect against brute force attacks
5. **Regular backups**: Automated daily/weekly backups
6. **Monitor logs**: Check for suspicious activity
7. **Keep secrets secret**: Never commit .env to git
8. **Use HTTPS only**: Redirect all HTTP to HTTPS
9. **Limit API access**: Use rate limiting (already configured)
10. **Update dependencies**: Regular security updates

---

## Support

For issues or questions:

- Check logs: `/var/log/webgst/`
- Review systemd journal: `sudo journalctl -u webgst`
- Test endpoints: `curl http://localhost:8000/health`

---

**Congratulations! Your WebGST application is now production-ready! 🎉**
