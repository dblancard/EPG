"""Show channel details and analyze overlaps for a given channel id.

Usage:
  python scripts/show_channel_by_id.py 11243
"""
import argparse
import sqlite3


def main():
    p = argparse.ArgumentParser()
    p.add_argument("channel_id", type=int, help="Database channel id")
    p.add_argument("--limit", type=int, default=50, help="Max programs to display")
    args = p.parse_args()

    conn = sqlite3.connect("epg.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name, channel_id FROM channels WHERE id=?", (args.channel_id,))
    ch = cur.fetchone()
    if not ch:
        print(f"Channel id {args.channel_id} not found")
        return
    print(f"Channel DB id={ch['id']}, name={ch['name']}, source_id='{ch['channel_id']}'\n")

    cur.execute(
        """
        SELECT id, title, start_time, end_time, COALESCE(category,'') AS category, COALESCE(description,'') AS description
        FROM programs
        WHERE channel_id=?
        ORDER BY start_time
        """,
        (args.channel_id,),
    )
    rows = cur.fetchall()
    print(f"Total programs: {len(rows)}\n")

    # Naive overlap analysis
    overlaps = []
    for i in range(1, len(rows)):
        prev = rows[i-1]
        curp = rows[i]
        if curp[2] < prev[3]:  # start_time < previous end_time
            overlaps.append((prev, curp))
    print(f"Overlapping adjacent pairs: {len(overlaps)}\n")

    if overlaps:
        print("Examples (up to 20):")
        for pair in overlaps[:20]:
            a, b = pair
            print(f"- [{a['id']}] {a['title']}  {a['start_time']} -> {a['end_time']}")
            print(f"  overlaps with")
            print(f"  [{b['id']}] {b['title']}  {b['start_time']} -> {b['end_time']}\n")

    print("First programs:")
    for r in rows[:args.limit]:
        print(f"  [{r['id']}] {r['title']}  {r['start_time']} -> {r['end_time']}")


if __name__ == "__main__":
    main()
