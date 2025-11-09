# EPG Web Service - Ubuntu Server Deployment Guide

This guide covers deploying the EPG Web Service on Ubuntu Server for production use.

## Prerequisites

- Ubuntu Server 20.04 LTS or newer
- Root or sudo access
- Internet connection for package installation

## Quick Start (Using GitHub)

```bash
# Clone the repository and run setup
git clone https://github.com/dblancard/EPG.git /home/epg/app
cd /home/epg/app
python3 -m venv venv
source venv/bin/activate
pip install -e .
python scripts/init_db.py
```

## Installation Steps

### 1. System Updates and Dependencies

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install Python 3.10+ and development tools
sudo apt install -y python3 python3-pip python3-venv git

# Install optional dependencies for better performance
sudo apt install -y build-essential libssl-dev libffi-dev
```

### 2. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -r -m -s /bin/bash epg
sudo usermod -aG sudo epg
```

### 3. Clone Repository from GitHub

```bash
# Switch to epg user
sudo su - epg

# Clone your repository
cd /home/epg
git clone https://github.com/dblancard/EPG.git app
cd app

# Verify files
ls -la
# You should see: src/, scripts/, pyproject.toml, README.md, etc.
```

### 4. Python Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the application in editable mode
pip install -e .

# Verify installation
python -c "import epg_web; print('EPG Web installed successfully')"
```

### 5. Initialize Database

```bash
# Still as epg user with venv activated
cd /home/epg/app

# Initialize the database with EPG data
python scripts/init_db.py

# This will:
# - Create epg.db in the current directory
# - Fetch and import EPG data from the default source
# - May take a few minutes depending on data size
```

### 6. Setup Systemd Service

Create a systemd service file to run the application automatically:

```bash
# Exit epg user back to your admin user
exit

# Create systemd service file
sudo nano /etc/systemd/system/epg-web.service
```

Paste this configuration:

```ini
[Unit]
Description=EPG Web Service
After=network.target

[Service]
Type=simple
User=epg
Group=epg
WorkingDirectory=/home/epg/app
Environment="PATH=/home/epg/app/venv/bin"
ExecStart=/home/epg/app/venv/bin/uvicorn epg_web.main:app --host 0.0.0.0 --port 8000 --workers 2

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=epg-web

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/epg/app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable epg-web

# Start the service
sudo systemctl start epg-web

# Check status
sudo systemctl status epg-web

# View logs
sudo journalctl -u epg-web -f
```

### 7. Setup Nginx Reverse Proxy (Recommended)

Install and configure Nginx as a reverse proxy:

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/epg-web
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Increase timeout for long EPG imports
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;

    # Client body size for uploads
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static files
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        proxy_cache_valid 200 1h;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/epg-web /etc/nginx/sites-enabled/

# Remove default site if desired
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx
```

### 8. Firewall Configuration

```bash
# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (if you'll use SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 9. Setup SSL with Let's Encrypt (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Certbot will automatically configure Nginx for HTTPS
# Test automatic renewal
sudo certbot renew --dry-run
```

## Post-Installation

### Verify Installation

```bash
# Check service status
sudo systemctl status epg-web

# Check logs
sudo journalctl -u epg-web -n 50

# Test the application
curl http://localhost:8000/api/countries
```

### Access the Application

Open your browser and navigate to:
- Local: `http://YOUR_SERVER_IP`
- With domain: `http://your-domain.com`
- With SSL: `https://your-domain.com`

## Maintenance Tasks

### Update EPG Data

```bash
# Manual update
sudo su - epg
cd /home/epg/app
source venv/bin/activate
python scripts/init_db.py
exit
```

### Setup Automatic Daily Updates with Cron

```bash
# Edit crontab for epg user
sudo crontab -u epg -e

# Add this line to update EPG data daily at 2 AM
0 2 * * * /home/epg/app/venv/bin/python /home/epg/app/scripts/init_db.py >> /home/epg/app/epg-update.log 2>&1
```

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u epg-web -f

# Last 100 lines
sudo journalctl -u epg-web -n 100

# Logs from today
sudo journalctl -u epg-web --since today

# Logs with error level
sudo journalctl -u epg-web -p err
```

### Restart Service

```bash
# Restart the service
sudo systemctl restart epg-web

# View status
sudo systemctl status epg-web
```

### Update Application Code

```bash
# On Ubuntu server
sudo su - epg
cd /home/epg/app

# Pull latest changes from GitHub
git pull origin main

# Activate venv and reinstall
source venv/bin/activate
pip install -e .

# Exit back to admin user
exit

# Restart service
sudo systemctl restart epg-web
```

### Backup Database

```bash
# Create backup directory
sudo mkdir -p /home/epg/backups

# Manual backup
sudo su - epg
cd /home/epg/app
cp epg.db /home/epg/backups/epg-$(date +%Y%m%d-%H%M%S).db
exit

# Automatic daily backup with cron
sudo crontab -u epg -e
# Add this line:
0 3 * * * cp /home/epg/app/epg.db /home/epg/backups/epg-$(date +\%Y\%m\%d).db
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Check database size
du -h /home/epg/app/epg.db

# Clean old backups (keep last 7 days)
find /home/epg/backups -name "epg-*.db" -mtime +7 -delete
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status epg-web

# Check logs for errors
sudo journalctl -u epg-web -n 50

# Verify Python environment
sudo su - epg
cd /home/epg/app
source venv/bin/activate
python -c "import epg_web"
uvicorn epg_web.main:app --host 0.0.0.0 --port 8000
```

### Database Locked Errors

```bash
# Stop the service
sudo systemctl stop epg-web

# Check for stale connections
sudo lsof | grep epg.db

# Rebuild database
sudo su - epg
cd /home/epg/app
source venv/bin/activate
rm epg.db
python scripts/init_db.py
exit

# Start service
sudo systemctl start epg-web
```

### High Memory Usage

```bash
# Check memory usage
free -h
top -u epg

# Reduce workers in systemd service
sudo nano /etc/systemd/system/epg-web.service
# Change --workers 2 to --workers 1

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart epg-web
```

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000
sudo netstat -tulpn | grep 8000

# Kill the process or change port in systemd service
```

## Performance Optimization

### Database Optimization

```bash
sudo su - epg
cd /home/epg/app
source venv/bin/activate

# Run SQLite optimization
sqlite3 epg.db "VACUUM; ANALYZE;"
exit
```

### Enable HTTP/2 in Nginx

Edit `/etc/nginx/sites-available/epg-web`:

```nginx
server {
    listen 443 ssl http2;
    # ... rest of configuration
}
```

### Add Response Compression

Add to Nginx configuration:

```nginx
# Enable gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
gzip_min_length 1000;
```

## Security Best Practices

1. **Change Default EPG URL** if it contains credentials:
   ```bash
   sudo nano /home/epg/app/src/epg_web/services/fetcher.py
   # Update DEFAULT_EPG_URL or use environment variable
   ```

2. **Use Environment Variables** for sensitive data:
   ```bash
   sudo nano /etc/systemd/system/epg-web.service
   # Add under [Service]:
   Environment="EPG_URL=your_secure_url"
   ```

3. **Regular Updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Fail2ban for SSH Protection**:
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   ```

## Uninstallation

If you need to remove the application:

```bash
# Stop and disable service
sudo systemctl stop epg-web
sudo systemctl disable epg-web
sudo rm /etc/systemd/system/epg-web.service
sudo systemctl daemon-reload

# Remove Nginx configuration
sudo rm /etc/nginx/sites-enabled/epg-web
sudo rm /etc/nginx/sites-available/epg-web
sudo systemctl restart nginx

# Remove application and user
sudo userdel -r epg

# Remove firewall rules if desired
sudo ufw delete allow 80/tcp
```

## Support and Resources

- Application logs: `sudo journalctl -u epg-web -f`
- Nginx logs: `/var/log/nginx/error.log` and `/var/log/nginx/access.log`
- Check service status: `sudo systemctl status epg-web`
- Test configuration: `sudo nginx -t`

---
Last updated: November 2025
