"""Show channel(s) and programs by name substring.

Usage examples:
  python scripts/show_channel.py AMC
  python scripts/show_channel.py "US| AMC"

Options:
  --limit N    Limit programs listed per channel (default 20)

Note: Looks up channels where name LIKE %<term>%. Prints basic channel info
and the first N programs ordered by start_time.
"""
import argparse
import sqlite3
from textwrap import shorten


def main():
    parser = argparse.ArgumentParser(description="Show channel(s) and programs by name substring")
    parser.add_argument("term", help="Substring to match in channel name (case-insensitive)")
    parser.add_argument("--limit", type=int, default=20, help="Max programs to list per channel")
    args = parser.parse_args()

    term = args.term
    limit = args.limit

    conn = sqlite3.connect("epg.db")
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, channel_id
            FROM channels
            WHERE UPPER(name) LIKE UPPER(?)
            ORDER BY name COLLATE NOCASE
            """,
            (f"%{term}%",),
        )
        channels = cur.fetchall()
        if not channels:
            print(f"No channels found matching '{term}'.")
            return

        print(f"Found {len(channels)} channel(s) matching '{term}':\n")
        for ch_id, name, source_id in channels:
            print(f"Channel: {name} (id={ch_id}, channel_id={source_id})")
            # Count programs
            cur.execute(
                "SELECT COUNT(*) FROM programs WHERE channel_id = ?",
                (ch_id,),
            )
            total = cur.fetchone()[0]
            print(f"  Total programs: {total}")

            # List first N programs ordered by start time
            cur.execute(
                """
                SELECT title, start_time, end_time, COALESCE(category, ''), COALESCE(description, '')
                FROM programs
                WHERE channel_id = ?
                ORDER BY start_time
                LIMIT ?
                """,
                (ch_id, limit),
            )
            rows = cur.fetchall()
            if not rows:
                print("  (no programs)\n")
                continue

            print("  Programs:")
            for title, st, et, category, desc in rows:
                cat = f" [{category}]" if category else ""
                desc_short = shorten(desc, width=80, placeholder="…") if desc else ""
                print(f"   - {title}{cat}")
                print(f"     {st} -> {et}")
                if desc_short:
                    print(f"     {desc_short}")
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
