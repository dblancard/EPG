"""EPG file parser module."""
import json
from datetime import datetime
from typing import Union

import xmltodict

from epg_web.models.schemas import ChannelCreate, EPGData, ProgramCreate

async def parse_epg_file(content: bytes, filename: str) -> EPGData:
    """Parse an EPG file (XML or JSON) and return structured data."""
    try:
        # Try to parse as XML first since we're dealing with XMLTV data
        data = xmltodict.parse(content)
        return parse_xmltv(data)
    except Exception as xml_error:
        try:
            # If XML parsing fails, try JSON
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            data = json.loads(content)
            return parse_json(data)
        except Exception as json_error:
            raise ValueError(f"Failed to parse EPG file: XML error: {xml_error}, JSON error: {json_error}")

def parse_xmltv(data: dict) -> EPGData:
    """Parse XMLTV format data."""
    if "tv" not in data:
        raise ValueError("Invalid XMLTV format: missing 'tv' element")
    
    tv_data = data["tv"]
    channels = []
    channel_map = {}  # Map XMLTV channel IDs to database IDs
    
    # Parse channels
    channel_list = tv_data.get("channel", [])
    if not isinstance(channel_list, list):
        channel_list = [channel_list]
    
    for channel in channel_list:
        channel_id = channel.get("@id", "")
        if not channel_id:
            continue
            
        # Clean and standardize the channel ID
        clean_channel_id = str(channel_id).strip()
        
        display_name = channel.get("display-name", "")
        if isinstance(display_name, list):
            display_name = display_name[0]
        if isinstance(display_name, dict):
            display_name = display_name.get("#text", "Unknown")
            
        icon_url = None
        if "icon" in channel:
            icon = channel["icon"]
            if isinstance(icon, dict):
                icon_url = icon.get("@src")
            elif isinstance(icon, list):
                icon_url = icon[0].get("@src") if icon else None
        
        # Create channel object with cleaned ID
        channel_data = ChannelCreate(
            name=display_name,
            channel_id=clean_channel_id,
            icon_url=icon_url
        )
        channels.append(channel_data)
        channel_map[clean_channel_id] = channel_data  # Map using cleaned ID
    
    # Parse programs
    programs = []
    program_list = tv_data.get("programme", [])
    if not isinstance(program_list, list):
        program_list = [program_list]
    
    for idx, program in enumerate(program_list):
        channel_id = program.get("@channel", "")
        if channel_id not in channel_map:
            continue  # Skip programs for unknown channels
            
        title = program.get("title", "")
        if isinstance(title, list):
            title = title[0]
        if isinstance(title, dict):
            title = title.get("#text", "Unknown")
            
        desc = program.get("desc", "")
        if isinstance(desc, list):
            desc = desc[0]
        if isinstance(desc, dict):
            desc = desc.get("#text", "")
            
        category = program.get("category", "")
        if isinstance(category, list) and category:
            # Use the first category and extract text if it's a dict
            category = category[0].get("#text", "") if isinstance(category[0], dict) else category[0]
        elif isinstance(category, dict):
            category = category.get("#text", "")
        
        try:
            # Clean and validate the channel ID
            clean_channel_id = str(channel_id).strip()
            channel = channel_map.get(clean_channel_id)
            
            if channel:
                programs.append(ProgramCreate(
                    title=title,
                    description=desc,
                    start_time=parse_xmltv_time(program.get("@start", "")),
                    end_time=parse_xmltv_time(program.get("@stop", "")),
                    category=category,
                    channel_id=clean_channel_id
                ))
            else:
                continue
        except (ValueError, KeyError) as e:
            continue
    
    return EPGData(channels=channels, programs=programs)

def parse_json(data: dict) -> EPGData:
    """Parse JSON format data."""
    if "channels" not in data or "programs" not in data:
        raise ValueError("Invalid JSON format: missing 'channels' or 'programs'")
    
    channels = [
        ChannelCreate(
            name=channel["name"],
            channel_id=channel["id"],
            icon_url=channel.get("iconUrl")
        )
        for channel in data["channels"]
    ]
    
    programs = [
        ProgramCreate(
            title=program["title"],
            description=program.get("description"),
            start_time=datetime.fromisoformat(program["startTime"]),
            end_time=datetime.fromisoformat(program["endTime"]),
            category=program.get("category"),
            # normalize channel id to string to match XMLTV parsing behavior
            channel_id=str(program["channelId"])
        )
        for program in data["programs"]
    ]
    
    return EPGData(channels=channels, programs=programs)

def parse_xmltv_time(time_str: str) -> datetime:
    """Parse XMLTV time format to UTC naive datetime.

    Supported inputs:
    - "YYYYMMDDHHMMSS +HHMM" (XMLTV with explicit offset)
    - "YYYYMMDDHHMMSS" (no offset) -> assumed UTC
    """
    if not time_str:
        raise ValueError("Missing time value")

    s = str(time_str).strip()
    parts = s.split()
    base = parts[0]
    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    # default to UTC if no offset provided
    from datetime import timezone, timedelta
    tzinfo = timezone.utc
    if len(parts) > 1:
        tz = parts[1]
        # Expect formats like +0000 or -0500
        if (len(tz) == 5) and (tz[0] in "+-") and tz[1:].isdigit():
            sign = 1 if tz[0] == "+" else -1
            hours = int(tz[1:3])
            minutes = int(tz[3:5])
            offset = timedelta(hours=hours, minutes=minutes) * sign
            tzinfo = timezone(offset)
    # attach tz and convert to UTC, then return naive UTC
    aware = dt.replace(tzinfo=tzinfo)
    dt_utc = aware.astimezone(timezone.utc)
    return dt_utc.replace(tzinfo=None)