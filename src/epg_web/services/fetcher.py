"""EPG data fetching service."""
import asyncio
import aiohttp

# Default EPG source URL
DEFAULT_EPG_URL = "http://vpn.modetv.ink/xmltv.php?username=rz8c28z5wu&password=tj5rvj6f2x"


async def fetch_epg_data(url: str = DEFAULT_EPG_URL) -> bytes:
    """Fetch EPG data from a URL.

    Args:
        url: The URL to fetch EPG data from, defaults to DEFAULT_EPG_URL

    Returns:
        bytes: The raw EPG data

    Raises:
        ValueError: If the URL is invalid or the request fails
    """
    timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds timeout
    conn = aiohttp.TCPConnector(verify_ssl=False)  # Skip SSL verification if needed

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch EPG data: HTTP {response.status}")
                data = await response.read()
                return data
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to fetch EPG data: {str(e)}")
        except asyncio.TimeoutError:
            raise ValueError("Timeout while fetching EPG data")
        except Exception as e:
            raise ValueError(f"Unexpected error while fetching EPG data: {str(e)}")


async def update_epg_from_url(url: str = DEFAULT_EPG_URL) -> dict:
    """Update EPG data from a URL.

    Args:
        url: The URL to fetch EPG data from

    Returns:
        dict: Summary of the update operation
    """
    from epg_web.epg.parser import parse_epg_file
    from epg_web.services.storage import get_session
    from epg_web.models.db import Channel, Program
    from sqlalchemy import delete

    # Fetch and parse the EPG data
    content = await fetch_epg_data(url)
    epg_data = await parse_epg_file(content, url.lower())

    async with get_session() as session:
        # Clear existing data
        await session.execute(delete(Program))
        await session.execute(delete(Channel))
        await session.flush()

        # Create new channel records and store in dictionary by channel_id string
        db_channels = {}  # Map channel_id to Channel object
        for idx, channel_data in enumerate(epg_data.channels):
            try:
                # Clean and standardize the channel ID
                clean_channel_id = str(channel_data.channel_id).strip()
                
                channel = Channel(
                    name=channel_data.name,
                    channel_id=clean_channel_id,  # Use cleaned ID
                    icon_url=channel_data.icon_url
                )
                session.add(channel)
                db_channels[clean_channel_id] = channel  # Store using cleaned ID
            except Exception as e:
                print(f"ERROR creating channel {channel_data.name}: {e}")

        # Flush to get channel IDs
        await session.flush()

        # Group programs by channel for merging consecutive identical entries
        from collections import defaultdict
        programs_by_channel = defaultdict(list)
        skipped = 0
        seen_unknown = set()

        for idx, program_data in enumerate(epg_data.programs):
            try:
                # Clean and standardize the program's channel ID for lookup
                clean_channel_id = str(program_data.channel_id).strip()
                
                if clean_channel_id not in db_channels:
                    if clean_channel_id not in seen_unknown:
                        seen_unknown.add(clean_channel_id)
                    skipped += 1
                    continue

                channel = db_channels[clean_channel_id]
                programs_by_channel[channel.id].append(program_data)

            except Exception as e:
                print(f"ERROR processing program {program_data.title}: {e}")
                skipped += 1
                continue

        # Merge consecutive identical programs per channel
        mapped = 0
        merged_count = 0
        for channel_id, program_list in programs_by_channel.items():
            # Sort by start_time
            program_list.sort(key=lambda p: p.start_time)
            
            merged_programs = []
            for prog in program_list:
                # Check if we can merge with the last merged program
                if merged_programs:
                    last = merged_programs[-1]
                    # Merge if: same title, same description (or both None/empty), same category,
                    # and time ranges are connected (overlap or touch)
                    desc_match = (last.description or "").strip() == (prog.description or "").strip()
                    cat_match = (last.category or "").strip() == (prog.category or "").strip()
                    title_match = last.title.strip() == prog.title.strip()
                    # Consider connected if the next starts at or before the last ends
                    connected = prog.start_time <= last.end_time
                    
                    if title_match and desc_match and cat_match and connected:
                        # Extend the last program's end time to cover the union
                        if prog.end_time > last.end_time:
                            last.end_time = prog.end_time
                        merged_count += 1
                        continue
                
                # No merge: add as new
                merged_programs.append(prog)
            
            # Insert merged programs into DB
            for prog_data in merged_programs:
                try:
                    program = Program(
                        title=prog_data.title,
                        description=prog_data.description,
                        start_time=prog_data.start_time,
                        end_time=prog_data.end_time,
                        category=prog_data.category,
                        channel_id=channel_id
                    )
                    session.add(program)
                    mapped += 1

                    # Commit in batches to avoid memory issues
                    if mapped % 1000 == 0:
                        await session.flush()

                except Exception as e:
                    print(f"ERROR creating program {prog_data.title}: {e}")
                    continue

        try:
            await session.commit()
            print(f"Merged {merged_count} consecutive identical programs.")
            return {
                "channels": len(db_channels),
                "programs": mapped,
                "merged": merged_count,
                "skipped": skipped,
                "unmapped_channels": len(seen_unknown)
            }
        except Exception as e:
            print(f"ERROR during final commit: {e}")
            raise