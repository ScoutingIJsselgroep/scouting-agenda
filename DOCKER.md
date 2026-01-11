# Docker Quick Start

## Snelle Setup (5 minuten)

### 1. Clone repository

```bash
git clone https://github.com/ScoutingIJsselgroep/scouting-agenda.git
cd scouting-agenda
```

### 2. Configureer secrets

```bash
cp secrets.yaml.example secrets.yaml
nano secrets.yaml  # Voeg je ICS URLs toe
```

### 3. Start met Docker Compose

```bash
docker-compose up -d
```

✅ **Klaar!** Server draait op http://localhost:8000

## Kalenders gebruiken

- **Verhuur**: http://localhost:8000/verhuur.ics
- **Welpen**: http://localhost:8000/welpen.ics
- **Scouts**: http://localhost:8000/scouts.ics

Kopieer deze URLs en voeg ze toe aan je kalender app (Google Calendar, Apple Calendar, Outlook, etc.)

## Handige commando's

```bash
# Logs bekijken
docker-compose logs -f

# Alleen server logs
docker-compose logs -f scouting-calendar

# Alleen sync logs
docker-compose logs -f scouting-calendar-sync

# Herstarten
docker-compose restart

# Stoppen
docker-compose down

# Update naar nieuwste versie
docker-compose pull
docker-compose up -d
```

## Configuratie aanpassen

Edit `config.yaml` voor:
- Andere kalenders toevoegen
- Visibility levels aanpassen
- Emoji's toevoegen
- Metadata wijzigen

**Na wijziging:**
```bash
docker-compose restart
```

## Troubleshooting

**Server start niet:**
```bash
docker-compose logs scouting-calendar
```

**Kalenders updaten niet:**
```bash
docker-compose logs scouting-calendar-sync
```

**Port 8000 al in gebruik:**
```yaml
# In docker-compose.yml wijzig:
ports:
  - "8001:8000"  # Gebruik poort 8001
```

**Secrets niet gevonden:**
```bash
# Check of secrets.yaml bestaat en volumes correct zijn
ls -la secrets.yaml
docker-compose config  # Valideer compose file
```

## Pre-built Image gebruiken (zonder builden)

Als je niet zelf wilt builden, gebruik de pre-built image van GHCR:

```yaml
# docker-compose.yml
services:
  scouting-calendar:
    image: ghcr.io/ScoutingIJsselgroep/scouting-agenda:latest
    # ... rest blijft hetzelfde
```

```bash
docker-compose pull
docker-compose up -d
```

## Productie Tips

1. **Gebruik volumes voor persistence:**
   ```yaml
   volumes:
     - calendar-data:/app/output
   ```

2. **Zet achter reverse proxy (Nginx/Caddy) voor HTTPS**

3. **Monitor met healthcheck:**
   ```bash
   docker-compose ps
   ```

4. **Backup je config:**
   ```bash
   cp config.yaml config.yaml.backup
   cp secrets.yaml secrets.yaml.backup
   ```

5. **Update regelmatig:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```
