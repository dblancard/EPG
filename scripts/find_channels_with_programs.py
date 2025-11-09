"""Find channels with programs."""
import sqlite3

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

# Get channels with program counts
print('Channels with programs (first 20):')
cursor.execute('''
    SELECT c.id, c.name, c.channel_id, COUNT(p.id) as program_count
    FROM channels c
    LEFT JOIN programs p ON c.id = p.channel_id
    GROUP BY c.id, c.name, c.channel_id
    HAVING program_count > 0
    ORDER BY c.id
    LIMIT 20
''')

for row in cursor.fetchall():
    print(f'  id={row[0]}, name={row[1][:30]}, channel_id={row[2]}, programs={row[3]}')

# Get total counts
print('\nSummary:')
cursor.execute('SELECT COUNT(*) FROM channels')
total_channels = cursor.fetchone()[0]
print(f'  Total channels: {total_channels}')

cursor.execute('''
    SELECT COUNT(DISTINCT c.id)
    FROM channels c
    INNER JOIN programs p ON c.id = p.channel_id
''')
channels_with_programs = cursor.fetchone()[0]
print(f'  Channels with programs: {channels_with_programs}')
print(f'  Channels without programs: {total_channels - channels_with_programs}')

conn.close()
