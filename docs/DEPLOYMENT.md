# Deployment Guide

## Production Deployment

### Docker Compose (Aanbevolen)

#### 1. Voorbereiding

```bash
# Clone repository
git clone https://github.com/ScoutingIJsselgroep/scouting-agenda.git
cd scouting-agenda

# Create secrets
cp secrets.yaml.example secrets.yaml
nano secrets.yaml  # Vul ICS URLs in

# Optioneel: pas config.yaml aan
nano config.yaml
```

#### 2. Start Services

```bash
docker-compose up -d
```

Dit start:
- **scouting-calendar**: FastAPI server op poort 8000
- **scouting-calendar-sync**: Automatische sync elke 10 minuten

#### 3. Verify

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/welpen.ics
```

#### 4. Updates

```bash
# Pull latest image
docker-compose pull

# Restart
docker-compose up -d
```

### Pre-built Images (GHCR)

Gebruik pre-built images van GitHub Container Registry:

```yaml
# docker-compose.yml
services:
  scouting-calendar:
    image: ghcr.io/scoutingijsselgroep/scouting-agenda:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./secrets.yaml:/app/secrets.yaml:ro
      - calendar-data:/app/output
    restart: unless-stopped
    environment:
      - TZ=Europe/Amsterdam

volumes:
  calendar-data:
```

```bash
docker-compose pull
docker-compose up -d
```

### Reverse Proxy (Nginx)

Voor HTTPS en custom domain:

```nginx
# /etc/nginx/sites-available/agenda.scouting-ijsselgroep.nl
server {
    listen 80;
    server_name agenda.scouting-ijsselgroep.nl;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agenda.scouting-ijsselgroep.nl;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/agenda.scouting-ijsselgroep.nl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agenda.scouting-ijsselgroep.nl/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Docker
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Cache ICS files (short TTL)
    location ~ \.ics$ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        
        # Cache for 5 minutes
        proxy_cache_valid 200 5m;
        proxy_cache_bypass $http_cache_control;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

**Setup SSL:**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d agenda.scouting-ijsselgroep.nl

# Enable site
sudo ln -s /etc/nginx/sites-available/agenda.scouting-ijsselgroep.nl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Caddy (Alternatief)

Caddy heeft automatic HTTPS:

```caddyfile
# Caddyfile
agenda.scouting-ijsselgroep.nl {
    reverse_proxy localhost:8000
    
    @ics path *.ics
    header @ics Cache-Control "public, max-age=300"
}
```

```bash
caddy run --config Caddyfile
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/scouting-agenda

# Deploy
gcloud run deploy scouting-agenda \
  --image gcr.io/PROJECT_ID/scouting-agenda \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8000
```

**Mount secrets:**
- Create Secret Manager secrets voor `config.yaml` en `secrets.yaml`
- Mount als volumes in Cloud Run

### AWS ECS

```yaml
# task-definition.json
{
  "family": "scouting-agenda",
  "containerDefinitions": [
    {
      "name": "server",
      "image": "ghcr.io/scoutingijsselgroep/scouting-agenda:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "TZ", "value": "Europe/Amsterdam"}
      ],
      "mountPoints": [
        {
          "sourceVolume": "config",
          "containerPath": "/app/config.yaml"
        }
      ]
    }
  ]
}
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scouting-calendar
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scouting-calendar
  template:
    metadata:
      labels:
        app: scouting-calendar
    spec:
      containers:
      - name: server
        image: ghcr.io/scoutingijsselgroep/scouting-agenda:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: secrets
          mountPath: /app/secrets.yaml
          subPath: secrets.yaml
        - name: output
          mountPath: /app/output
      
      - name: sync
        image: ghcr.io/scoutingijsselgroep/scouting-agenda:latest
        command: ["sh", "-c", "while true; do python sync.py; sleep 600; done"]
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: secrets
          mountPath: /app/secrets.yaml
          subPath: secrets.yaml
        - name: output
          mountPath: /app/output
      
      volumes:
      - name: config
        configMap:
          name: calendar-config
      - name: secrets
        secret:
          secretName: calendar-secrets
      - name: output
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: scouting-calendar
spec:
  selector:
    app: scouting-calendar
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring

### Health Checks

```bash
# Server health
curl https://agenda.scouting-ijsselgroep.nl/

# Specific calendar
curl -I https://agenda.scouting-ijsselgroep.nl/welpen.ics
```

### Logs

**Docker:**
```bash
docker-compose logs -f
docker-compose logs --tail=100 scouting-calendar
```

**Systemd (als je systemd gebruikt):**
```bash
journalctl -u scouting-calendar -f
```

### Metrics (Prometheus)

Voeg Prometheus metrics toe aan server.py:

```python
from prometheus_client import Counter, Histogram, generate_latest

calendar_requests = Counter('calendar_requests_total', 'Total calendar requests', ['calendar'])
response_time = Histogram('response_time_seconds', 'Response time')
```

## Backup & Restore

### Config Backup

```bash
# Backup
cp config.yaml config.yaml.backup
cp secrets.yaml secrets.yaml.backup

# Restore
cp config.yaml.backup config.yaml
cp secrets.yaml.backup secrets.yaml
```

### Automated Backup

```bash
# Cron job (daily backup)
0 2 * * * cd /path/to/scouting-agenda && tar czf backup-$(date +\%Y\%m\%d).tar.gz config.yaml secrets.yaml output/
```

## Security

### Secrets Management

**Productie:** Gebruik secret management:
- **Docker Secrets**: `docker secret create`
- **Kubernetes Secrets**: `kubectl create secret`
- **Cloud Secret Managers**: AWS Secrets Manager, GCP Secret Manager

### Network Security

- Run achter reverse proxy met HTTPS
- Gebruik firewall rules
- Enable rate limiting
- Monitor voor unusual activity

### Updates

```bash
# Check for updates
docker-compose pull

# Apply updates
docker-compose up -d

# Verify
docker-compose ps
curl https://agenda.scouting-ijsselgroep.nl/
```

## Performance

### Caching

Gebruik Cloudflare of Nginx caching:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=calendar_cache:10m max_size=100m inactive=60m;

location ~ \.ics$ {
    proxy_cache calendar_cache;
    proxy_cache_valid 200 5m;
    add_header X-Cache-Status $upstream_cache_status;
}
```

### Sync Optimization

Pas sync interval aan in `docker-compose.yml`:

```yaml
command: >
  sh -c "while true; do
    python sync.py;
    sleep 1800;  # 30 minuten
  done"
```

## Troubleshooting

**Service doesn't start:**
```bash
docker-compose logs
docker-compose ps
```

**SSL issues:**
```bash
sudo certbot renew --dry-run
sudo systemctl status nginx
```

**Performance issues:**
- Check sync logs voor errors
- Verify ICS source URLs
- Monitor disk space
- Check memory usage: `docker stats`

**Calendar not updating:**
```bash
# Force sync
docker-compose exec scouting-calendar-sync python sync.py --verbose

# Check output
docker-compose exec scouting-calendar ls -lh /app/output/
```
