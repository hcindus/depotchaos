#!/bin/bash
# DepotChaos Settings Restore Script
# Generated: 2026-06-08
# Version: 1.0.0

echo "=========================================="
echo "  DepotChaos Settings Restore"
echo "  $(date)"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPOTCHAOS_ROOT="/root/.openclaw/workspace/DepotChaos"
DATADEPOT_WEB="/root/.openclaw/workspace/datadepot/web"
WEB_ROOT="/var/www/psdepot.com/depotchaos"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SYSTEMD="/etc/systemd/system"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Function to confirm action
confirm() {
    read -p "Proceed with $1? (y/N): " choice
    case "$choice" in
        y|Y ) echo "Proceeding..."; return 0;;
        * ) echo "Skipped."; return 1;;
    esac
}

# ========================================
# 1. Restore Systemd Services
# ========================================
restore_services() {
    echo -e "${YELLOW}Step 1: Restoring Systemd Services${NC}"
    
    # DepotChaos FastAPI Service
    if confirm "create depotchaos-fastapi.service"; then
        cat > "$SYSTEMD/depotchaos-fastapi.service" << 'EOF'
[Unit]
Description=DepotChaos CRM FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/datadepot/web
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/datadepot/web/depotchaos_fastapi.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=MAILGUN_TEST_MODE=True
Environment=MAILGUN_DOMAIN=psdepot.com

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable depotchaos-fastapi.service
        echo -e "${GREEN}✓ depotchaos-fastapi.service created${NC}"
    fi

    # DepotChaos Auto-Enrichment Service
    if confirm "create depotchaos-enrichment.service"; then
        cat > "$SYSTEMD/depotchaos-enrichment.service" << 'EOF'
[Unit]
Description=DepotChaos Auto-Enrichment Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/DepotChaos/auto_enrichment_daemon.py
Restart=always
RestartSec=60
User=root

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable depotchaos-enrichment.service
        echo -e "${GREEN}✓ depotchaos-enrichment.service created${NC}"
    fi

    echo ""
}

# ========================================
# 2. Restore Nginx Configurations
# ========================================
restore_nginx() {
    echo -e "${YELLOW}Step 2: Restoring Nginx Configurations${NC}"
    
    if confirm "create depotchaos.psdepot.com nginx config"; then
        cat > "$NGINX_AVAILABLE/depotchaos.psdepot.com" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name depotchaos.psdepot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen [::]:443 ssl;
    listen 443 ssl;
    server_name depotchaos.psdepot.com;
    
    root /var/www/psdepot.com/depotchaos;
    index index.html;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/psdepot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/psdepot.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # DepotChaos API endpoints
    location /api {
        proxy_pass http://localhost:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Main page
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF
        
        # Enable site
        ln -sf "$NGINX_AVAILABLE/depotchaos.psdepot.com" "$NGINX_ENABLED/depotchaos.psdepot.com"
        nginx -t && systemctl reload nginx
        echo -e "${GREEN}✓ depotchaos.psdepot.com nginx config created${NC}"
    fi

    echo ""
}

# ========================================
# 3. Create Directories
# ========================================
restore_directories() {
    echo -e "${YELLOW}Step 3: Creating Directories${NC}"
    
    mkdir -p "$DEPOTCHAOS_ROOT"
    mkdir -p "$DEPOTCHAOS_ROOT/enrichment_queue"
    mkdir -p "$WEB_ROOT/static"
    mkdir -p "/root/.openclaw/workspace/data/depot_chaos"
    mkdir -p "/root/.openclaw/workspace/datadepot/queue"
    
    echo -e "${GREEN}✓ Directories created${NC}"
    echo ""
}

# ========================================
# 4. Start Services
# ========================================
start_services() {
    echo -e "${YELLOW}Step 4: Starting Services${NC}"
    
    systemctl daemon-reload
    systemctl start depotchaos-fastapi.service 2>/dev/null || true
    systemctl start depotchaos-enrichment.service 2>/dev/null || true
    
    echo -e "${GREEN}✓ Services started${NC}"
    echo ""
    
    # Show status
    echo "Current service status:"
    systemctl status depotchaos-fastapi.service --no-pager -l 2>/dev/null | head -5 || echo "depotchaos-fastapi: not found"
    echo ""
}

# ========================================
# 5. Verify Installation
# ========================================
verify_installation() {
    echo -e "${YELLOW}Step 5: Verifying Installation${NC}"
    echo ""
    
    # Check API
    echo "Testing API endpoint..."
    curl -s http://localhost:8082/api/stats 2>/dev/null || echo "API not responding (may need time to start)"
    echo ""
    
    # Check directories
    echo "Directory structure:"
    ls -la "$DEPOTCHAOS_ROOT" 2>/dev/null | head -10
    echo ""
    
    # Check database
    if [[ -f "$DEPOTCHAOS_ROOT/depot_chaos.db" ]]; then
        echo -e "${GREEN}✓ depot_chaos.db exists${NC}"
    else
        echo -e "${YELLOW}⚠ depot_chaos.db not found${NC}"
    fi
    
    if [[ -f "/root/.openclaw/workspace/data/depot_chaos/unified.db" ]]; then
        echo -e "${GREEN}✓ unified.db exists${NC}"
    else
        echo -e "${YELLOW}⚠ unified.db not found${NC}"
    fi
    
    echo ""
}

# ========================================
# Main Menu
# ========================================
main_menu() {
    echo "Select an option:"
    echo "  1) Full restore (all steps)"
    echo "  2) Restore services only"
    echo "  3) Restore nginx only"
    echo "  4) Create directories only"
    echo "  5) Start services only"
    echo "  6) Verify only"
    echo "  0) Exit"
    echo ""
    read -p "Choice: " choice
    
    case "$choice" in
        1)
            restore_directories
            restore_services
            restore_nginx
            start_services
            verify_installation
            ;;
        2)
            restore_services
            ;;
        3)
            restore_nginx
            ;;
        4)
            restore_directories
            ;;
        5)
            start_services
            ;;
        6)
            verify_installation
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
}

# Run main menu
main_menu

echo ""
echo "=========================================="
echo "  DepotChaos Restore Complete"
echo "=========================================="
echo ""
echo "URLs:"
echo "  CRM:      https://depotchaos.psdepot.com"
echo "  API:      https://depotchaos.psdepot.com/api/stats"
echo ""
echo "Commands:"
echo "  systemctl status depotchaos-fastapi"
echo "  systemctl status depotchaos-enrichment"
echo ""
