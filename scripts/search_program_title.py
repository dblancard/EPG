"""Search programs by (case-insensitive) title substring, optionally within a channel.

Usage:
  python scripts/search_program_title.py --title "Lethal Weapon 2"
  python scripts/search_program_title.py --title "Lethal Weapon 2" --channel-id 9428
"""
import argparse
import sqlite3


def main():
    p = argparse.ArgumentParser(description="Search programs by title substring")
    p.add_argument("--title", required=True, help="Title substring (case-insensitive)")
    p.add_argument("--channel-id", type=int, help="Optional channel id to filter")
    args = p.parse_args()

    conn = sqlite3.connect("epg.db")
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if args.channel_id:
            cur.execute(
                """
                SELECT p.id, p.title, p.start_time, p.end_time, c.id as channel_id, c.name as channel_name
                FROM programs p JOIN channels c ON p.channel_id = c.id
                WHERE c.id = ? AND UPPER(p.title) LIKE UPPER(?)
                ORDER BY p.start_time
                """,
                (args.channel_id, f"%{args.title}%"),
            )
        else:
            cur.execute(
                """
                SELECT p.id, p.title, p.start_time, p.end_time, c.id as channel_id, c.name as channel_name
                FROM programs p JOIN channels c ON p.channel_id = c.id
                WHERE UPPER(p.title) LIKE UPPER(?)
                ORDER BY c.name COLLATE NOCASE, p.start_time
                """,
                (f"%{args.title}%",),
            )
        rows = cur.fetchall()
        if not rows:
            print("No matches found.")
            return
        print(f"Found {len(rows)} program(s) matching '{args.title}':\n")
        for r in rows:
            print(f"[{r['id']}] {r['title']}  |  {r['start_time']} -> {r['end_time']}  |  Channel {r['channel_id']}: {r['channel_name']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
