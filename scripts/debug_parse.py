import asyncio

from epg_web.services.fetcher import fetch_epg_data, DEFAULT_EPG_URL
from epg_web.epg.parser import parse_epg_file

async def main():
    print(f"Fetching from {DEFAULT_EPG_URL}")
    data = await fetch_epg_data(DEFAULT_EPG_URL)
    epg = await parse_epg_file(data, DEFAULT_EPG_URL)
    print(f"Parsed {len(epg.channels)} channels and {len(epg.programs)} programs")
    print("First 10 channels (name, channel_id):")
    for c in epg.channels[:10]:
        print(repr((c.name, c.channel_id, c.icon_url)))
    print("First 10 programs (channel_id, title):")
    for p in epg.programs[:10]:
        print(repr((p.channel_id, p.title)))

if __name__ == '__main__':
    asyncio.run(main())
