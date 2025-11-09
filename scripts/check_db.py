"""Check database contents."""
import sqlite3

conn = sqlite3.connect('epg.db')
cursor = conn.cursor()

# Check counts
cursor.execute('SELECT COUNT(*) FROM programs')
program_count = cursor.fetchone()[0]
print(f'Total programs: {program_count}')

cursor.execute('SELECT COUNT(*) FROM channels')
channel_count = cursor.fetchone()[0]
print(f'Total channels: {channel_count}')

# Show sample channels
print('\nFirst 5 channels:')
cursor.execute('SELECT id, name, channel_id FROM channels LIMIT 5')
for row in cursor.fetchall():
    print(f'  id={row[0]}, name={row[1]}, channel_id={row[2]}')

# Show sample programs
print('\nFirst 5 programs:')
cursor.execute('SELECT id, title, channel_id FROM programs LIMIT 5')
for row in cursor.fetchall():
    print(f'  id={row[0]}, title={row[1]}, channel_id={row[2]}')

# Check if programs reference valid channels
print('\nChecking program-channel relationships:')
cursor.execute('''
    SELECT p.id, p.title, p.channel_id, c.name
    FROM programs p
    LEFT JOIN channels c ON p.channel_id = c.id
    LIMIT 10
''')
for row in cursor.fetchall():
    channel_name = row[3] if row[3] else 'NOT FOUND'
    print(f'  Program: {row[1]}, channel_id={row[2]}, channel_name={channel_name}')

conn.close()
