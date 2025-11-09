"""Extract a specific channel and its programs from the XMLTV feed."""
import asyncio
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from epg_web.services.fetcher import fetch_epg_data, DEFAULT_EPG_URL


def parse_xmltv_time(time_str):
    """Parse XMLTV time format to datetime object.
    
    XMLTV format: YYYYMMDDhhmmss +HHMM
    Example: 20251104020000 +0100
    """
    # Split time and timezone
    parts = time_str.strip().split()
    if len(parts) != 2:
        return None
    
    time_part = parts[0]
    tz_part = parts[1]
    
    # Parse the time
    dt = datetime.strptime(time_part, '%Y%m%d%H%M%S')
    
    # Parse timezone offset
    tz_sign = 1 if tz_part[0] == '+' else -1
    tz_hours = int(tz_part[1:3])
    tz_minutes = int(tz_part[3:5])
    tz_offset_minutes = tz_sign * (tz_hours * 60 + tz_minutes)
    
    # Create timezone
    tz = timezone(timedelta(minutes=tz_offset_minutes))
    dt = dt.replace(tzinfo=tz)
    
    return dt


def format_est_time(dt):
    """Convert datetime to EST and format as readable string."""
    if dt is None:
        return "N/A"
    
    # Convert to EST (-5 hours from UTC)
    est = timezone(timedelta(hours=-5))
    dt_est = dt.astimezone(est)
    
    # Format: Mon Nov 04, 2025 at 01:00 AM EST
    return dt_est.strftime('%a %b %d, %Y at %I:%M %p EST')


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


async def extract_channel_data(channel_id: str, output_file: str = None):
    """Extract channel and its programs from XMLTV feed.
    
    Args:
        channel_id: The channel ID to extract
        output_file: Output file path (default: channel_{id}.xml)
    """
    print(f"Fetching EPG data from {DEFAULT_EPG_URL}...")
    content = await fetch_epg_data(DEFAULT_EPG_URL)
    
    print(f"Parsing XMLTV data...")
    # Parse the XML
    root = ET.fromstring(content)
    
    # Create new root element
    tv_root = ET.Element('tv')
    tv_root.set('generator-info-name', 'EPG Channel Extractor')
    
    # Find and extract the channel
    channel_found = False
    for channel in root.findall('channel'):
        if channel.get('id') == channel_id:
            tv_root.append(channel)
            channel_found = True
            print(f"Found channel: {channel.get('id')}")
            # Print channel details
            display_name = channel.find('display-name')
            if display_name is not None:
                print(f"  Name: {display_name.text}")
            icon = channel.find('icon')
            if icon is not None:
                print(f"  Icon: {icon.get('src')}")
            break
    
    if not channel_found:
        print(f"ERROR: Channel {channel_id} not found in feed!")
        return
    
    # Find and extract all programs for this channel
    program_count = 0
    for programme in root.findall('programme'):
        if programme.get('channel') == channel_id:
            # Add EST time as comments
            start_time = programme.get('start')
            stop_time = programme.get('stop')
            
            if start_time:
                start_dt = parse_xmltv_time(start_time)
                est_start = format_est_time(start_dt)
                # Add as comment before the title
                comment = ET.Comment(f' EST: {est_start} ')
                programme.insert(0, comment)
            
            if stop_time:
                stop_dt = parse_xmltv_time(stop_time)
                est_stop = format_est_time(stop_dt)
                # Find title and insert comment after it
                title_elem = programme.find('title')
                if title_elem is not None:
                    title_index = list(programme).index(title_elem)
                    comment = ET.Comment(f' to {est_stop} ')
                    programme.insert(title_index + 1, comment)
            
            tv_root.append(programme)
            program_count += 1
    
    print(f"Found {program_count} programs for channel {channel_id}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = f"channel_{channel_id}.xml"
    
    output_path = Path(output_file)
    
    # Write pretty-printed XML
    print(f"Writing to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(prettify_xml(tv_root))
    
    print(f"Successfully extracted channel {channel_id} to {output_path}")
    print(f"  Channel: 1")
    print(f"  Programs: {program_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract a channel from XMLTV feed')
    parser.add_argument('channel_id', help='Channel ID to extract')
    parser.add_argument('-o', '--output', help='Output file path', default=None)
    
    args = parser.parse_args()
    
    asyncio.run(extract_channel_data(args.channel_id, args.output))
