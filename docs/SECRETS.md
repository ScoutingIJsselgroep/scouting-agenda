# Secrets & Environment Variables

Je kunt secrets (zoals ICS URLs en optionele wachtwoorden) definiëren in `secrets.yaml`, maar ook via environment variabelen.

- Prioriteit: environment variabele > `secrets.yaml`
- Formaat: `SECRET_<KEY_NAME_UPPERCASE>` (bijv. `SECRET_WELPEN_ICS_URL`)

Voorbeeld:

```bash
# Terminal
export SECRET_WELPEN_ICS_URL="https://.../welpen.ics"
export SECRET_GROEPSBREED_PASSWORD="mijn-geheime-wachtwoord"
```

In Docker Compose kun je deze toevoegen onder `environment`:

```yaml
services:
  scouting-calendar:
    environment:
      - SECRET_WELPEN_ICS_URL=https://.../welpen.ics
      - SECRET_GROEPSBREED_PASSWORD=mijn-geheime-wachtwoord
```

Dit is handig voor CI/CD, containers en om te voorkomen dat je gevoelige bestanden moet mounten zoals `secrets.yaml`.
