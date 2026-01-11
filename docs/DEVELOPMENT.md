# Development Guide

## Setup Development Environment

### 1. Clone Repository

```bash
git clone https://github.com/ScoutingIJsselgroep/scouting-agenda.git
cd scouting-agenda
```

### 2. Install Dependencies

```bash
# Create virtual environment
uv venv

# Activate
source .venv/bin/activate  # macOS/Linux
# of: .venv\Scripts\activate  # Windows

# Install dev dependencies (includes ruff)
uv pip install -e ".[dev]"
```

### 3. Configure Secrets

```bash
# Copy example
cp secrets.yaml.example secrets.yaml

# Edit with your ICS URLs
nano secrets.yaml
```

### 4. Install Pre-commit Hooks (optioneel)

```bash
pip install pre-commit
pre-commit install
```

## Project Structure

```
scouting-agenda/
├── scouting_agenda/         # Main package
│   ├── __init__.py
│   ├── sync_calendars.py    # Sync & merge logic
│   └── server.py            # FastAPI server
├── sync.py                  # Entry point: sync
├── run_server.py            # Entry point: server
├── config.yaml              # Calendar configuration
├── secrets.yaml             # ICS URLs (gitignored)
├── output/                  # Generated ICS files
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD
├── pyproject.toml          # Dependencies & ruff config
├── Dockerfile
├── docker-compose.yml
└── Makefile                # Dev shortcuts
```

## Code Quality

### Ruff Configuration

Ruff is configured in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM"]
ignore = ["E501"]
```

### Commands

```bash
# Lint
make lint
# of: ruff check .

# Auto-fix
make fix
# of: ruff check --fix .

# Format
make format
# of: ruff format .

# Check alles
make check
# of: ruff check . && ruff format --check .
```

### Pre-commit Hooks

Bij elke commit worden automatisch gerund:
- `ruff check --fix` - Linting met auto-fix
- `ruff format` - Code formatting
- Trailing whitespace check
- YAML validation
- Large file check

**Manual run:**
```bash
pre-commit run --all-files
```

## Running Locally

### Sync Calendars

```bash
# Basic sync
python sync.py

# Verbose output
python sync.py --verbose

# Sync specific calendar
python sync.py --calendar welpen

# Via make
make sync
```

### Start Server

```bash
# Basic server
python run_server.py

# Development mode (auto-reload)
uvicorn scouting_agenda.server:app --reload --host 0.0.0.0 --port 8000

# Via make
make server
```

Server draait op: http://localhost:8000

### Docker Development

```bash
# Build image
make docker-build

# Start containers
make docker-up

# View logs
make docker-logs

# Stop containers
make docker-down
```

## Testing

### Manual Testing

```bash
# Test sync
python sync.py --verbose

# Check output
ls -lh output/

# View calendar content
cat output/welpen.ics

# Test server
curl http://localhost:8000/
curl http://localhost:8000/welpen.ics
```

### Configuration Testing

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Test secret loading
python -c "from scouting_agenda.sync_calendars import load_config; load_config()"
```

## Making Changes

### Adding a New Calendar

1. **Update secrets.yaml:**
```yaml
nieuwe_speltak_ics_url: "https://calendar.google.com/..."
```

2. **Update config.yaml:**
```yaml
calendars:
  - name: nieuwe_speltak
    output: nieuwe_speltak.ics
    visibility: title_only
    sources:
      - url: !secret nieuwe_speltak_ics_url
        name: "Nieuwe Speltak"
        emoji: "🟣"
```

3. **Test:**
```bash
python sync.py --calendar nieuwe_speltak
ls output/nieuwe_speltak.ics
```

### Modifying Visibility

Edit `config.yaml` en wijzig `visibility`:
- `title_only` - Alleen titels
- `busy_only` - Alleen bezet/vrij
- `all_details` - Alle informatie

### Adding Emoji Support

In `config.yaml`:
```yaml
sources:
  - url: !secret welpen_ics_url
    name: "Welpen"
    emoji: "🐺"  # Optioneel
```

## Debugging

### Verbose Logging

```bash
python sync.py --verbose
```

### Check Configuration

```bash
python -c "
from scouting_agenda.sync_calendars import load_config
import json
config = load_config()
print(json.dumps(config, indent=2, default=str))
"
```

### Validate ICS Output

```bash
# Using icalendar library
python -c "
from icalendar import Calendar
with open('output/welpen.ics', 'rb') as f:
    cal = Calendar.from_ical(f.read())
    for event in cal.walk('vevent'):
        print(event.get('summary'))
"
```

### Docker Debugging

```bash
# Build with no cache
docker build --no-cache -t scouting-agenda:debug .

# Run with shell
docker run -it --rm scouting-agenda:debug /bin/bash

# Check logs
docker-compose logs -f scouting-calendar
docker-compose logs -f scouting-calendar-sync
```

## CI/CD

### GitHub Actions

Two workflows are configured:

**1. Lint (`lint.yml`)**
- Runs on push/PR
- Executes `ruff check` and `ruff format --check`

**2. Docker Build (`docker-build.yml`)**
- Builds multi-platform images (amd64, arm64)
- Pushes to GitHub Container Registry
- Triggers on push to main/master or version tags

### Local CI Testing

```bash
# Test lint workflow
make lint
make check

# Test Docker build
make docker-build
```

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/nieuwe-functie`
3. Make changes
4. Run linting: `make check`
5. Commit: `git commit -am 'Add nieuwe functie'`
6. Push: `git push origin feature/nieuwe-functie`
7. Create Pull Request

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints where possible
- Write docstrings for functions
- Keep functions small and focused
- Use descriptive variable names

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Reference issues when applicable (#123)
- Keep first line under 72 characters
- Add detailed description if needed

## Troubleshooting

**Secrets not loading:**
- Check `secrets.yaml` exists
- Validate YAML syntax
- Ensure keys match config.yaml references

**ICS fetch fails:**
- Check URL accessibility
- Verify timeout settings in config.yaml
- Check network/firewall

**Docker build fails:**
- Check Dockerfile syntax
- Verify all files exist (pyproject.toml, etc.)
- Clean build cache: `docker builder prune`

**Server won't start:**
- Check port 8000 is free: `lsof -i :8000`
- Verify config.yaml exists
- Check output directory permissions
