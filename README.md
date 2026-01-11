# Scouting Agenda - ICS Calendar Merger

Een systeem om meerdere iCal bronnen te mergen met configureerbare zichtbaarheid en te serveren via een eenvoudige API.

## Features

- **Configureerbaar via YAML**: Definieer meerdere kalenders met verschillende bronnen en zichtbaarheidsniveaus
- **Home Assistant style secrets**: Gebruik `!secret` tag om gevoelige URLs veilig op te slaan
- **Visibility filtering**: 
  - `title_only`: Alleen event titel zichtbaar
  - `busy_only`: Alleen bezet/vrij (geen details)
  - `all_details`: Alle event informatie
- **Automatische merge**: Combineer meerdere ICS bronnen tot één kalender
- **Deduplicatie**: Automatisch dubbele events detecteren en verwijderen
- **FastAPI server**: Serveer gegenereerde ICS bestanden via HTTP
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

## Configuratie

### 1. Secrets instellen (Home Assistant style)

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

```bash
# Run sync met debug output
python sync.py --verbose

# Server met auto-reload
uvicorn scouting_agenda.server:app --reload --host 0.0.0.0 --port 8000
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
