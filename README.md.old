# Scouting Agenda - ICS Calendar Merger

Een systeem om meerdere iCal bronnen te mergen met configureerbare zichtbaarheid en te serveren via een eenvoudige API.

## Features

- **Configureerbaar via YAML**: Definieer meerdere kalenders met verschillende bronnen en zichtbaarheidsniveaus
- **Home Assistant style secrets**: Gebruik `!secret` tag om gevoelige URLs veilig op te slaan
- **Emoji support**: Voeg optioneel emoji's toe aan events voor betere visuele herkenning
- **Visibility filtering**: 
  - `title_only`: Alleen event titel zichtbaar
  - `busy_only`: Alleen bezet/vrij (geen details)
  - `all_details`: Alle event informatie
- **Automatische merge**: Combineer meerdere ICS bronnen tot één kalender
- **Deduplicatie**: Automatisch dubbele events detecteren en verwijderen
- **FastAPI server**: Serveer gegenereerde ICS bestanden via HTTP
- **Docker ready**: Inclusief Dockerfile en docker-compose
- **GitHub Actions**: Automatische Docker builds bij elke push
- **Cron-ready**: Gebruik het sync script voor periodieke updates

## Project Structure

```
scouting-agenda/
├── config.yaml              # Hoofdconfiguratie
├── secrets.yaml             # Gevoelige URLs (niet committen!)
├── secrets.yaml.example     # Template voor secrets
├── sync.py                  # Entry point: sync script
├── run_server.py            # Entry point: start server
├── scouting_agenda/         # Python package
│   ├── __init__.py
│   ├── sync_calendars.py    # Merge script logica
│   └── server.py            # FastAPI server
├── output/                  # Gegenereerde ICS bestanden
│   ├── verhuur.ics
│   ├── welpen.ics
│   └── scouts.ics
├── requirements.txt
└── pyproject.toml
```

## Installatie

### Optie 1: Lokaal (Python)

```bash
# Maak virtual environment
uv venv

# Activeer environment
source .venv/bin/activate  # macOS/Linux
# of: .venv\Scripts\activate  # Windows

# Installeer dependencies
uv pip install -r requirements.txt

# Maak secrets bestand
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml met je eigen ICS URLs
```

### Optie 2: Docker (aangeraden voor productie)

```bash
# Build image
docker build -t scouting-agenda .

# Of gebruik docker-compose
docker-compose up -d
```

**Docker omgevingsvariabelen:**
- `TZ`: Tijdzone (default: `Europe/Amsterdam`)

**Docker volumes:**
- `/app/config.yaml`: Configuratie bestand (read-only)
- `/app/secrets.yaml`: Secrets bestand (read-only)
- `/app/output`: Output directory voor gegenereerde ICS bestanden

**Docker compose** start automatisch:
- Server op poort 8000
- Sync service die elke 10 minuten draait

### Optie 3: Pre-built Docker image (GitHub Container Registry)

```bash
# Pull de latest image
docker pull ghcr.io/ScoutingIJsselgroep/scouting-agenda:latest

# Run met docker-compose
docker-compose up -d
```

## Configuratie

### 1. Sec

### Docker (aangeraden)

```bash
# Start alles (server + sync)
docker-compose up -d

# Alleen server
docker-compose up -d scouting-calendar

# Logs bekijken
docker-compose logs -f

# Stop
docker-compose down
```

Kalenders beschikbaar op: `http://localhost:8000/verhuur.ics`

### Lokaal (Python)rets instellen (Home Assistant style)

Maak `secrets.yaml` aan met je gevoelige ICS URLs:

```yaml
# secrets.yaml (niet committen!)
welpen_ics_url: "https://calendar.google.com/calendar/ical/..."
scouts_ics_url: "https://nextcloud.example.com/remote.php/dav/..."
```

> **Let op**: `secrets.yaml` staat in `.gitignore` en wordt niet gecommit!

### 2. Config.yaml gebruiken

In `config.yaml` refereer je naar secrets met de `!secret` tag:

```yaml
calendars:
  - name: verhuur
    output: verhuur.ics
    visibility: title_only
    sources:
      - url: !secret welpen_ics_url
        name: "Welpen"
      - url: !secret scouts_ics_url
        name: "Scouts"
```

### 3. Visibility opties

- **`title_only`**: Toont alleen de event titel en tijdstip. Beschrijving, locatie, deelnemers etc. worden verwijderd.
- **`busy_only`**: Toont alleen bezet/vrij status. Event wordt omgezet naar "Bezet" zonder details.
- **`all_details`**: Alle event informatie wordt behouden (standaard).

## Gebruik

### 1. Eenmalig sync

```bash
python sync.py
# of via module:
python -m scouting_agenda.sync_calendars
```

Dit genereert alle ICS bestanden in de `output/` directory.

### 2. Server starten

```bash
python run_server.py
# of via module:
python -m scouting_agenda.server
```

Server draait op `http://localhost:8000`

Kalenders beschikbaar op:
- `http://localhost:8000/verhuur.ics`
- `http://localhost:8000/welpen.ics`
- `http://localhost:8000/scouts.ics`

### 3. Cron job (automatische sync)

Voeg toe aan crontab voor sync elke 10 minuten:

```bash
crontab -e
```

```cron
*/10 * * * * cd /path/to/scouting-agenda && /path/to/.venv/bin/python sync.py >> /tmp/calendar-sync.log 2>&1
```

### 4. Server als service (optioneel)

Voor productie gebruik, draai met systemd, supervisor, of Docker.

Voorbeeld systemd service (`/etc/systemd/system/calendar-server.service`):

```ini
[Unit]
Description=Calendar ICS Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/scouting-agenda
Environment="PATH=/path/to/scouting-agenda/.venv/bin"
ExecStart=/path/to/scouting-agenda/.venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## API Endpoints

### GET /{calendar}.ics

Serveer een gegenereerde ICS kalender.

**Voorbeeld:**
```bash
curl http://localhost:8000/verhuur.ics
```

### GET /

Health check en lijst van beschikbare kalenders.

**Response:**
```json
{
  "status": "ok",
  "calendars": ["verhuur.ics", "welpen.ics", "scouts.ics"]
}
```

### GET /sync

Trigger handmatige sync (optioneel, voor debugging).

## Development

### Setup

```bash
# Install dev dependencies (includes ruff)
uv pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Code Quality

**Ruff** is geconfigureerd voor linting en formatting:

```bash
# Lint code
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check formatting without changes
ruff format --check .
```

**Of gebruik Makefile shortcuts:**

```bash
make lint      # Run linter
make format    # Format code
make check     # Check lint + format
make fix       # Auto-fix + format
```

### Running

```bash
# Run sync met debug output
python sync.py --verbose

# Server met auto-reload
uvicorn scouting_agenda.server:app --reload --host 0.0.0.0 --port 8000

# Docker development build
docker build -t scouting-agenda:dev .
docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml -v $(pwd)/secrets.yaml:/app/secrets.yaml scouting-agenda:dev
```

### Pre-commit Hooks

Pre-commit hooks runnen automatisch ruff bij elke commit:

```bash
# Setup
pre-commit install

# Manual run
pre-commit run --all-files
```

## Deployment

### Docker met GitHub Actions

De repository bevat een GitHub Actions workflow die automatisch Docker images bouwt:

1. **Push naar main/master**: Bouwt en pusht `latest` tag
2. **Tag met `v*`**: Bouwt en pusht versioned tags (bijv. `v1.0.0`, `1.0`, `1`)
3. **Pull requests**: Bouwt maar pusht niet

**Images worden gepubliceerd naar GitHub Container Registry:**
```
ghcr.io/ScoutingIJsselgroep/scouting-agenda:latest
ghcr.io/ScoutingIJsselgroep/scouting-agenda:v1.0.0
```

**Gebruik in productie:**

```bash
# Maak docker-compose.yml met GHCR image
version: '3.8'
services:
  scouting-calendar:
    image: ghcr.io/ScoutingIJsselgroep/scouting-agenda:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./secrets.yaml:/app/secrets.yaml:ro
      - calendar-data:/app/output
    restart: unless-stopped

volumes:
  calendar-data:
```

### Kubernetes/Cloud

Het Docker image kan direct gebruikt worden in Kubernetes, Cloud Run, of andere container platforms.

**Voorbeeld Kubernetes deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scouting-calendar
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: server
        image: ghcr.io/ScoutingIJsselgroep/scouting-agenda:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: secrets
          mountPath: /app/secrets.yaml
          subPath: secrets.yaml
      volumes:
      - name: config
        configMap:
          name: calendar-config
      - name: secrets
        secret:
          name: calendar-secrets
```

## Home Assistant Integratie

Voeg kalenders toe in Home Assistant via Remote Calendar:

```yaml
# configuration.yaml
calendar:
  - platform: ical
    name: "Verhuur Lokaal"
    url: "http://192.168.1.100:8000/verhuur.ics"
  
  - platform: ical
    name: "Welpen"
    url: "http://192.168.1.100:8000/welpen.ics"
  
  - platform: ical
    name: "Scouts"
    url: "http://192.168.1.100:8000/scouts.ics"
```

## Troubleshooting

**Sync faalt:**
- Check of ICS URLs bereikbaar zijn
- Verhoog `timeout_seconds` in config.yaml
- Run met `--verbose` voor debug output

**Server start niet:**
- Check of poort 8000 vrij is
- Check output directory bestaat en schrijfbaar is

**Events missen:**
- Check of `visibility` correct is ingesteld
- Events met identieke UID worden gededupliceerd
- Check bron ICS bestanden handmatig

## License

MIT
