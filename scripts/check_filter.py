import asyncio
from epg_web.services.storage import get_session
from epg_web.models.db import Channel
from sqlalchemy import select, or_

async def check_filtered():
    prefixes = ['CA|','US|','UK|']
    async with get_session() as session:
        conds = [Channel.name.startswith(p) for p in prefixes]
        result = await session.execute(select(Channel).where(or_(*conds)).order_by(Channel.channel_id))
        channels = result.scalars().all()
        print(f"\nChannels matching prefixes {prefixes}: {len(channels)}")
        for ch in channels[:20]:
            print(f"- id={ch.id}, channel_id={ch.channel_id}, name={ch.name}")

if __name__ == '__main__':
    asyncio.run(check_filtered())
