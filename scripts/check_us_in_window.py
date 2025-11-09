"""Check US channels with programs in current viewing window."""
from datetime import datetime, timedelta
import sqlite3

now = datetime.now()
start = now - timedelta(hours=1)
# Round start to nearest 30 min
mins = start.minute
rounded_mins = 0 if mins < 30 else 30
start = start.replace(minute=rounded_mins, second=0, microsecond=0)
end = start + timedelta(hours=6)

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

print(f"Current time: {now}")
print(f"Time window: {start} to {end}")
print()

cursor.execute("""
    SELECT c.id, c.name, COUNT(p.id) as prog_count
    FROM channels c 
    JOIN programs p ON c.id = p.channel_id 
    WHERE c.name LIKE 'US|%' 
      AND p.end_time > ? 
      AND p.start_time < ?
    GROUP BY c.id 
    ORDER BY prog_count DESC 
    LIMIT 20
""", (start.isoformat(), end.isoformat()))

results = cursor.fetchall()
print(f"US channels with programs in current viewing window: {len(results)}")
print()
for row in results:
    print(f"  {row[1]}: {row[2]} programs (id={row[0]})")

conn.close()
