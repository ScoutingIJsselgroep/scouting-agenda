# API Documentation

## Endpoints

### `GET /`

Health check en lijst van beschikbare kalenders.

**Response:**
```json
{
  "status": "ok",
  "message": "Scouting Calendar Server",
  "calendars": ["welpen.ics", "scouts.ics", "explorers.ics", ...],
  "configured": [
    {
      "name": "welpen",
      "file": "welpen.ics",
      "visibility": "title_only",
      "sources_count": 2
    },
    ...
  ],
  "output_dir": "/app/output"
}
```

### `GET /{calendar}.ics`

Download een ICS kalender bestand.

**Parameters:**
- `calendar` (path): Naam van de kalender (bijv. `welpen`, `scouts`)

**Voorbeeld:**
```bash
curl https://agenda.scouting-ijsselgroep.nl/welpen.ics
```

**Response Headers:**
- `Content-Type: text/calendar; charset=utf-8`
- `Content-Disposition: inline; filename="welpen.ics"`
- `Cache-Control: no-cache, must-revalidate`

**Status Codes:**
- `200`: Kalender gevonden en geserveerd
- `404`: Kalender niet gevonden

### `GET /api/calendars`

Metadata van alle geconfigureerde kalenders.

**Response:**
```json
{
  "calendars": [
    {
      "name": "welpen",
      "file": "welpen.ics",
      "url": "/welpen.ics",
      "visibility": "title_only",
      "sources": [
        {"name": "Welpen", "url": "https://..."},
        {"name": "Groepsactiviteiten", "url": "https://..."}
      ],
      "exists": true,
      "size_bytes": 1234,
      "modified": 1704931200.0
    }
  ]
}
```

### `GET /api/sync`

Trigger handmatige sync (voor debugging).

**Let op:** In productie gebruik een cron job voor automatische sync.

**Response:**
```json
{
  "status": "completed",
  "returncode": 0,
  "stdout": "...",
  "stderr": "..."
}
```

**Status Codes:**
- `200`: Sync succesvol
- `500`: Sync gefaald of timeout

## Kalender Abonneren

### In Google Calendar

1. Ga naar [Google Calendar](https://calendar.google.com)
2. Klik op **+** naast "Andere agenda's"
3. Kies **Via URL**
4. Plak de ICS URL: `https://agenda.scouting-ijsselgroep.nl/welpen.ics`
5. Klik **Toevoegen**

### In Apple Calendar (macOS/iOS)

1. Open **Agenda** app
2. **Bestand** → **Nieuw agenda-abonnement**
3. Plak de ICS URL: `https://agenda.scouting-ijsselgroep.nl/welpen.ics`
4. Klik **Abonneren**

### In Outlook

1. Ga naar **Agenda**
2. **Agenda toevoegen** → **Abonneren op internet**
3. Plak de ICS URL: `https://agenda.scouting-ijsselgroep.nl/welpen.ics`
4. Klik **Importeren**

### In Home Assistant

```yaml
# configuration.yaml
calendar:
  - platform: ical
    name: "Welpen"
    url: "https://agenda.scouting-ijsselgroep.nl/welpen.ics"
  
  - platform: ical
    name: "Scouts"
    url: "https://agenda.scouting-ijsselgroep.nl/scouts.ics"
```

## Technische Details

### Visibility Levels

De server ondersteunt verschillende zichtbaarheidsniveaus:

**`title_only`** (aanbevolen voor lezers):
- Toont alleen event titel en tijdstip
- Beschrijving, locatie en deelnemers worden verwijderd
- Voegt source naam toe aan titel (bijv. "Welpen: Weekendkamp")
- Optioneel: emoji prefix

**`busy_only`**:
- Toont alleen bezet/vrij status
- Event titel wordt "Bezet"
- Geen details zichtbaar

**`all_details`** (alleen voor leiding):
- Alle event informatie behouden
- Volledige beschrijving, locatie, deelnemers
- Source marker toegevoegd
