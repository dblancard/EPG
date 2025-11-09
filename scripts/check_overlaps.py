"""Scan the SQLite database for overlapping programs per channel.

Usage (from project root with venv active):
  python scripts/check_overlaps.py

Outputs a summary and lists channels with overlaps, showing the conflicting items.
"""
import asyncio
from dataclasses import dataclass
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from epg_web.services.storage import get_session
from epg_web.models.db import Channel, Program


@dataclass
class Overlap:
    channel_id: int
    channel_name: str
    a_id: int
    a_title: str
    a_start: str
    a_end: str
    b_id: int
    b_title: str
    b_start: str
    b_end: str
    minutes_overlap: int


async def find_overlaps(session: AsyncSession) -> Tuple[int, List[Overlap]]:
    total_overlaps = 0
    overlaps: List[Overlap] = []

    # Get all channels
    channels = (await session.execute(select(Channel))).scalars().all()

    for ch in channels:
        # Fetch channel programs ordered by start
        progs = (
            await session.execute(
                select(Program)
                .where(Program.channel_id == ch.id)
                .order_by(Program.start_time, Program.end_time)
            )
        ).scalars().all()

        if len(progs) < 2:
            continue

        prev = progs[0]
        for cur in progs[1:]:
            # Overlap if current starts before previous ends
            if cur.start_time < prev.end_time:
                # overlap duration in minutes
                delta = int((prev.end_time - cur.start_time).total_seconds() // 60)
                total_overlaps += 1
                overlaps.append(
                    Overlap(
                        channel_id=ch.id,
                        channel_name=ch.name,
                        a_id=prev.id,
                        a_title=prev.title,
                        a_start=str(prev.start_time),
                        a_end=str(prev.end_time),
                        b_id=cur.id,
                        b_title=cur.title,
                        b_start=str(cur.start_time),
                        b_end=str(cur.end_time),
                        minutes_overlap=delta,
                    )
                )
                # Advance prev: keep the later end to catch deep overlaps
                prev = prev if prev.end_time >= cur.end_time else cur
            else:
                prev = cur

    return total_overlaps, overlaps


async def main():
    async with get_session() as session:
        total, overlaps = await find_overlaps(session)
        print(f"Total overlapping pairs detected: {total}")
        if not overlaps:
            return

        # Group by channel for readability
        from collections import defaultdict
        by_channel = defaultdict(list)
        for o in overlaps:
            by_channel[(o.channel_id, o.channel_name)].append(o)

        for (cid, cname), items in by_channel.items():
            print("\n=== Channel:", cname, f"(id={cid}) ===")
            for o in items[:50]:  # limit output per channel
                print(
                    f" - Overlap {o.minutes_overlap}m:"
                    f" [{o.a_id}] '{o.a_title}' ({o.a_start} -> {o.a_end})"
                    f" with [{o.b_id}] '{o.b_title}' ({o.b_start} -> {o.b_end})"
                )
            if len(items) > 50:
                print(f"   ... truncated, {len(items)-50} more overlaps ...")


if __name__ == "__main__":
    asyncio.run(main())
