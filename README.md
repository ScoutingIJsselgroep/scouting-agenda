# Scouting IJsselgroep - Agenda Systeem

Een systeem om meerdere Google Calendar agendas samen te voegen en te delen met ouders en leiding, zonder driedubbele administratie.

## 📋 Waarom?

Bij Scouting IJsselgroep hebben we verschillende agenda's voor elke speltak, groepsactiviteiten en kader. We willen:

- **Eén bron van waarheid**: Leiding beheert hun eigen speltak agenda + groepsagenda
- **Geen dubbel werk**: Activiteiten maar één keer invoeren
- **Privacy-bewust delen**: Ouders zien alleen relevante info voor hun speltak
- **Automatische synchronisatie**: Wijzigingen zijn direct zichtbaar

### Hoe werkt het?

**Voor leiding (bewerkersrechten):**

Je krijgt toegang tot de volgende **Google Calendars** (waarin je activiteiten kunt toevoegen/bewerken):
- **Je eigen speltak** (bijv. Welpen, Scouts, Explorers)
- **Groepsagenda** (overkoepelende activiteiten zoals kampvuren, scoutingfeest)
- **Kader** (leidingoverleg, groepsraad, klusdag, etc.)

**Voor ouders/leden (lezers):**

Je abonneert op een ICS link die automatisch wordt gegenereerd:
- Bijvoorbeeld: `https://agenda.scouting-ijsselgroep.nl/welpen.ics`
- Deze bevat automatisch je speltak + groepsactiviteiten
- Alleen titel en tijdstip zichtbaar (privacy-friendly)
- Synchroniseert automatisch in je eigen agenda app

## 📅 Beschikbare Agenda's

| Agenda | Bronnen | Zichtbaarheid | URL |
|--------|---------|---------------|-----|
| **Welpen** | Welpen + Groepsactiviteiten | Alleen titel | `agenda.scouting-ijsselgroep.nl/welpen.ics` |
| **Scouts** | Scouts + Groepsactiviteiten | Alleen titel | `agenda.scouting-ijsselgroep.nl/scouts.ics` |
| **Explorers** | Explorers + Groepsactiviteiten | Alle details | `agenda.scouting-ijsselgroep.nl/explorers.ics` |
| **Roverscouts** | Roverscouts + Groepsactiviteiten | Alle details | `agenda.scouting-ijsselgroep.nl/roverscouts.ics` |
| **Stam** | Stam + Groepsactiviteiten | Alle details | `agenda.scouting-ijsselgroep.nl/stam.ics` |
| **Groepsbreed** | Alle speltakken + Groepsactiviteiten + Kader | Alle details + emoji's | `agenda.scouting-ijsselgroep.nl/groepsbreed.ics` |

### Emoji Legend (Groepsbreed)
- 🟢 Welpen
- 🟡 Scouts
- 🟠 Explorers
- 🔴 Roverscouts
- 🔵 Stam
- ⚪ Groepsactiviteiten
- 🟣 Kader

## 🚀 Quick Start

### Voor Ouders/Leden

1. Kopieer de ICS link voor jouw speltak (zie tabel hierboven)
2. Voeg toe aan je agenda app:

**Google Calendar:**
- Ga naar [Google Calendar](https://calendar.google.com)
- Klik **+** naast "Andere agenda's"
- Kies **Via URL**
- Plak de link
- Klik **Toevoegen**

**Apple Calendar (iPhone/Mac):**
- Open **Agenda** app
- **Bestand** → **Nieuw agenda-abonnement** (Mac) of **Instellingen** → **Agenda's** → **Account toevoegen** → **Overige** (iPhone)
- Plak de link
- Klik **Abonneren**

**Outlook:**
- Ga naar **Agenda**
- **Agenda toevoegen** → **Abonneren op internet**
- Plak de link
- Klik **Importeren**

De agenda synchroniseert automatisch!

## 🛠️ Voor Leiding: Setup

### Optie 1: Docker (Aanbevolen)

```bash
# 1. Clone repository
git clone https://github.com/ScoutingIJsselgroep/scouting-agenda.git
cd scouting-agenda

# 2. Configureer secrets (vraag ICS URLs aan beheerder)
cp secrets.yaml.example secrets.yaml
nano secrets.yaml

# 3. Start services
docker-compose up -d
```

✅ Server draait op http://localhost:8000

Zie [Docker Quick Start](docs/DOCKER.md) voor meer details.

### Optie 2: Lokaal (Python)

```bash
# 1. Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .

# 2. Configureer secrets
cp secrets.yaml.example secrets.yaml
nano secrets.yaml

# 3. Run sync
sync

# 4. Start server
server
```

## 📖 Documentatie

- **[API Documentatie](docs/API.md)** - Endpoints, kalender abonneren
- **[Docker Guide](docs/DOCKER.md)** - Docker setup en troubleshooting
- **[Development](docs/DEVELOPMENT.md)** - Ontwikkelomgeving, code style
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment, Nginx, Kubernetes
 - **[Secrets & Env Vars](docs/SECRETS.md)** - Gebruik van secrets via `secrets.yaml` of environment variabelen

## 🔧 Configuratie

### Agenda Toevoegen

Bewerk `config.yaml`:

```yaml
calendars:
  - name: nieuwe_speltak
    output: nieuwe_speltak.ics
    visibility: title_only  # of: busy_only, all_details
    sources:
      - url: !secret nieuwe_speltak_ics_url
        name: "Nieuwe Speltak"
        emoji: "🟣"  # Optioneel
```

### Zichtbaarheidsniveaus

- **`title_only`**: Alleen titel + tijd (voor ouders/leden)
- **`busy_only`**: Alleen bezet/vrij status
- **`all_details`**: Alle informatie (voor leiding)

Zie [config.yaml](config.yaml) voor volledig overzicht.

## 🔒 Privacy & Beveiliging

- **Secrets gescheiden**: ICS URLs in `secrets.yaml` (niet in git)
- **Privacy-niveaus**: Ouders zien alleen titel, geen gevoelige details
- **Read-only voor leden**: ICS links zijn alleen-lezen
- **HTTPS**: In productie achter Nginx/Caddy met SSL

## 🤝 Bijdragen

Zie [DEVELOPMENT.md](docs/DEVELOPMENT.md) voor development setup.

Code style:
- Python 3.12+
- Ruff voor linting en formatting
- Type hints waar mogelijk
- Docstrings voor functies

```bash
# Check code quality
make lint
make format
```

## 📝 License

MIT License - zie [LICENSE](LICENSE) bestand.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/ScoutingIJsselgroep/scouting-agenda/issues)
- **Email**: [tristan@scouting-ijsselgroep.nl](mailto:tristan@scouting-ijsselgroep.nl)

## 🙏 Credits

Gebouwd met:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [iCalendar](https://icalendar.readthedocs.io/) - ICS parsing/generation
- [Ruff](https://docs.astral.sh/ruff/) - Linting en formatting
- [Docker](https://www.docker.com/) - Containerization

---

**Scouting IJsselgroep** | [Website](https://scouting-ijsselgroep.nl) | [Facebook](https://facebook.com/scoutingijsselgroep)
