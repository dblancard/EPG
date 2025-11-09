# README.md - EPG Web Service

# EPG Web Service

[![CI](https://github.com/dblancard/EPG/actions/workflows/ci.yml/badge.svg)](https://github.com/dblancard/EPG/actions/workflows/ci.yml)
[![Deploy](https://github.com/dblancard/EPG/actions/workflows/deploy.yml/badge.svg)](https://github.com/dblancard/EPG/actions/workflows/deploy.yml)
![License](https://img.shields.io/github/license/dblancard/EPG)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Last commit](https://img.shields.io/github/last-commit/dblancard/EPG)

# README.md - EPG Web Service

This is an Electronic Program Guide (EPG) web service that provides the following features:
1. EPG data feed parsing (XML/JSON)
2. Program data storage in SQLite database
3. REST API for querying TV program information
4. Web interface for viewing the TV guide

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dblancard/EPG.git
cd epg-web
```

2. Install the package in development mode:
```bash
pip install -e .
```

3. Initialize the database:
```bash
python scripts/init_db.py
```

## Usage

1. Start the FastAPI development server:
```bash
# With minimal logging (recommended for production/testing), accessible on LAN
uvicorn epg_web.main:app --host 0.0.0.0 --port 8000 --reload --log-level warning

# Or with full logging (for debugging)
uvicorn epg_web.main:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** Using `--host 0.0.0.0` makes the server accessible from other devices on your network.
- Local access: http://localhost:8000
- LAN access: http://YOUR_IP_ADDRESS:8000 (find your IP with `ipconfig` on Windows)

2. Access the application:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Documentation: http://localhost:8000/redoc

## Features

### API Endpoints

- `POST /api/upload`: Upload EPG data file (XML/JSON)
- `GET /api/channels`: List all channels
- `GET /api/schedule/{channel_id}`: Get program schedule for a channel

### Supported EPG Formats

1. XMLTV Format
```xml
<tv>
  <channel id="channel.1">
    <display-name>Channel One</display-name>
    <icon src="http://example.com/icon.png"/>
  </channel>
  <programme channel="channel.1" start="20240215180000 +0000" stop="20240215190000 +0000">
    <title>Show Title</title>
    <desc>Show Description</desc>
    <category>Show Category</category>
  </programme>
</tv>
```

2. JSON Format
```json
{
  "channels": [
    {
      "id": "channel.1",
      "name": "Channel One",
      "iconUrl": "http://example.com/icon.png"
    }
  ],
  "programs": [
    {
      "channelId": "channel.1",
      "title": "Show Title",
      "description": "Show Description",
      "startTime": "2024-02-15T18:00:00Z",
      "endTime": "2024-02-15T19:00:00Z",
      "category": "Show Category"
    }
  ]
}
```

## Development

### Project Structure

```
epg_web/
      If you're deploying via GitHub Actions to a server, ensure the following repository secrets are set (Settings > Secrets and variables > Actions):

      | Secret | Description |
      |--------|-------------|
      | SSH_HOST | Public IP or DNS of your Ubuntu server |
      | SSH_PORT | SSH port (default 22) |
      | SSH_USER | SSH user (e.g. epg) |
      | SSH_KEY  | Private key contents (PEM) for SSH_USER |
      | APP_DIR  | Absolute path target (e.g. /home/epg/app) |

      The `deploy.yml` workflow will:
      1. Rsync the repository to `$APP_DIR`
      2. Create/update a Python virtual environment
      3. Install dependencies with `pip install -e .`
      4. Initialize the database if missing
      5. Restart the systemd service `epg-web`

├── src/epg_web/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   ├── epg/
│   │   ├── __init__.py
│   │   └── parser.py        # EPG file parser
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py           # SQLAlchemy models
│   │   └── schemas.py      # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   └── storage.py      # Database operations
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── index.html
├── tests/
├── scripts/
│   └── init_db.py
└── pyproject.toml
```

## Testing

Run the tests with pytest:
```bash
pytest tests/
```

## License

[Your chosen license]