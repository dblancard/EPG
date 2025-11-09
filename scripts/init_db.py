"""Initialize the database and load EPG data."""
import asyncio

from epg_web.services.storage import init_db
from epg_web.services.fetcher import update_epg_from_url, DEFAULT_EPG_URL

async def main():
    """Initialize the database and load EPG data."""
    # Initialize database schema
    await init_db()
    print("Database initialized successfully!")
    
    # Fetch and load EPG data from the default source
    try:
        print(f"Fetching EPG data from {DEFAULT_EPG_URL}...")
        result = await update_epg_from_url()
        print(f"Successfully imported {result['channels']} channels and {result['programs']} programs.")
    except Exception as e:
        import traceback
        print(f"Error loading EPG data: {repr(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())