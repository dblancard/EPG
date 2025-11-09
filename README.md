# README.md - EPG Web Service

This is an Electronic Program Guide (EPG) web service that provides the following features:
1. EPG data feed parsing (XML/JSON)
2. Program data storage in SQLite database
3. REST API for querying TV program information
4. Web interface for viewing the TV guide

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
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