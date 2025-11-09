"""Check programs for a specific channel."""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

channel_id = 10696

# Get channel info
cursor.execute("SELECT id, name, channel_id FROM channels WHERE id = ?", (channel_id,))
ch = cursor.fetchone()
print(f"Channel: {ch[1]} (id={ch[0]}, channel_id={ch[2]})")

# Get all programs for this channel
cursor.execute("""
    SELECT title, start_time, end_time, description
    FROM programs 
    WHERE channel_id = ?
    ORDER BY start_time
""", (channel_id,))

programs = cursor.fetchall()
print(f"\nTotal programs: {len(programs)}")
print("\nProgram times:")
for prog in programs:
    print(f"  {prog[0]}")
    print(f"    Start: {prog[1]}")
    print(f"    End: {prog[2]}")
    print()

conn.close()
