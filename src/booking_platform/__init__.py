def main() -> None:
    """Start the API on http://127.0.0.1:8000 (the PostgreSQL container must be running)."""
    from .app import main as run

    run()
