"""Check database schema and relationships."""
import sqlite3

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

# Get channel schema
print('CHANNELS table schema:')
cursor.execute('PRAGMA table_info(channels)')
for row in cursor.fetchall():
    print(f'  {row}')

print('\nPROGRAMS table schema:')
cursor.execute('PRAGMA table_info(programs)')
for row in cursor.fetchall():
    print(f'  {row}')

# Check a specific example
print('\nChannel id=1:')
cursor.execute('SELECT id, name, channel_id FROM channels WHERE id = 1')
channel = cursor.fetchone()
print(f'  id={channel[0]}, name={channel[1]}, channel_id={channel[2]}')

print('\nPrograms for channel id=1 (using id):')
cursor.execute('SELECT COUNT(*) FROM programs WHERE channel_id = 1')
count = cursor.fetchone()[0]
print(f'  Count: {count}')

print('\nPrograms for channel id=5118 (channel_id from first program):')
cursor.execute('SELECT COUNT(*) FROM programs WHERE channel_id = 5118')
count = cursor.fetchone()[0]
print(f'  Count: {count}')

print('\nChannel with database id=5118:')
cursor.execute('SELECT id, name, channel_id FROM channels WHERE id = 5118')
channel = cursor.fetchone()
if channel:
    print(f'  id={channel[0]}, name={channel[1]}, channel_id={channel[2]}')
else:
    print('  NOT FOUND')

conn.close()
