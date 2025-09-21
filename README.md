# Photo Archivist

An intelligent photo archival and printing system that helps you manage, deduplicate, and print your best photos using OneDrive as a source and Kite's print service for testing.

## Features

- Microsoft Account integration for OneDrive photo access (read-only)
- Monthly/quarterly automated syncs using Graph API delta queries
- Intelligent photo scoring using:
  - Sharpness (Laplacian variance)
  - Exposure balance
  - Perceptual hash deduplication
- Web-based UI with HTMX for interactivity
- Test mode print orders via Kite API (no charges)

## Requirements

- Python 3.9 or higher
- Microsoft Azure App registration with:
  - Redirect URI: http://localhost:8000/auth/callback
  - Required permissions: Files.Read, offline_access
- Kite API test credentials
- SQLite 3.x

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/photo-archivist.git
   cd photo-archivist
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux:
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Create and configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your Microsoft App registration and Kite API test credentials.

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open http://localhost:8000 in your browser

## Configuration

See `.env.example` for all available configuration options. Key settings:

- `MSAL_*`: Microsoft authentication settings
- `GRAPH_*`: OneDrive API settings
- `KITE_*`: Print service settings (using test mode)
- `SYNC_INTERVAL_MINUTES`: Default 43200 (monthly)
- `SHORTLIST_SIZE`: Default 20
- `DUPE_THRESHOLD`: pHash Hamming distance (default 5)

## Development

- Format code: `black app tests`
- Run linter: `ruff app tests`
- Type checking: `mypy app tests`
- Run tests: `pytest`
- Generate coverage: `pytest --cov=app --cov-report=html`

## Project Structure

```
photo-archivist/
  app/
    auth/         # MSAL authentication
    sync/         # OneDrive delta sync
    scoring/      # Photo scoring and dedupe
    shortlist/    # Shortlist management
    print/        # Kite print integration
    ui/           # Web UI (Jinja + HTMX)
    models/       # Database models
    telemetry/    # Logging utils
  tests/          # Test suite
  scripts/        # Utility scripts
```

## Limitations

- OneDrive is the only supported photo source
- Read-only access to photos (no modifications)
- SQLite database (no clustering support)
- Test-mode only for print orders
- No face detection/recognition in MVP
- English-only interface

## Security Notes

- Tokens are encrypted at rest
- No image files are stored locally
- Minimal metadata is persisted
- Test mode prevents accidental charges

## License

[Your chosen license]

## Contributing

[Your contribution guidelines]