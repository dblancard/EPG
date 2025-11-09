"""Check US channel contents."""
import sqlite3

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

# Check US channels
cursor.execute("SELECT COUNT(*) FROM channels WHERE name LIKE 'US|%'")
us_total = cursor.fetchone()[0]
print(f'Total US channels: {us_total}')

cursor.execute("""
    SELECT COUNT(DISTINCT c.id) 
    FROM channels c 
    JOIN programs p ON c.id = p.channel_id 
    WHERE c.name LIKE 'US|%'
""")
us_with_programs = cursor.fetchone()[0]
print(f'US channels with programs: {us_with_programs}')

# Show sample US channels
print('\nSample US channels:')
cursor.execute("SELECT id, name, channel_id FROM channels WHERE name LIKE 'US|%' LIMIT 10")
for row in cursor.fetchall():
    cursor.execute("SELECT COUNT(*) FROM programs WHERE channel_id = ?", (row[0],))
    prog_count = cursor.fetchone()[0]
    print(f'  id={row[0]}, name={row[1]}, channel_id={row[2]}, programs={prog_count}')

conn.close()
