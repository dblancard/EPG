"""Find US channels with most programs."""
import sqlite3

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT c.id, c.name, c.channel_id, COUNT(p.id) as pcount 
    FROM channels c 
    JOIN programs p ON c.id = p.channel_id 
    WHERE c.name LIKE 'US|%' 
    GROUP BY c.id 
    ORDER BY pcount DESC 
    LIMIT 10
""")

print('Top 10 US channels by program count:')
for row in cursor.fetchall():
    print(f'  id={row[0]}, name={row[1]}, channel_id={row[2]}, programs={row[3]}')

conn.close()
