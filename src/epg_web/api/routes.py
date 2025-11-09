"""API endpoints for the EPG web service."""
from typing import List
from pydantic import HttpUrl

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from sqlalchemy import select, func

from epg_web.models.db import Channel, Program
from epg_web.models.schemas import ChannelResponse, ProgramResponse, EPGSourceUpdate
from epg_web.services.storage import get_session
from epg_web.services.fetcher import update_epg_from_url
from epg_web.epg.parser import parse_epg_file

router = APIRouter(tags=["epg"])

@router.post("/upload")
async def upload_epg_file(file: UploadFile = File(...)):
    """Upload and parse an EPG file."""
    if not file.filename.endswith((".xml", ".json")):
        raise HTTPException(status_code=400, detail="Only XML and JSON files are supported")
    
    content = await file.read()
    try:
        epg_data = await parse_epg_file(content, file.filename)
        async with get_session() as session:
            # Store parsed data
            # Implementation to be added
            await session.commit()
        return {"message": "EPG data uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-from-url")
async def update_from_url(source: EPGSourceUpdate):
    """Update EPG data from a URL."""
    try:
        result = await update_epg_from_url(source.url)
        return {
            "message": "EPG data updated successfully",
            "channels_imported": result["channels"],
            "programs_imported": result["programs"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update EPG data: {str(e)}")

@router.get("/countries", response_model=dict)
async def get_countries():
    """Get list of available countries based on channel name prefixes."""
    async with get_session() as session:
        # Get all distinct country codes from channel names (2-char prefix before |)
        result = await session.execute(select(Channel.name))
        channels = result.scalars().all()
        
        countries = set()
        for name in channels:
            if '|' in name:
                code = name.split('|')[0].strip().upper()
                # Only accept 2-character country codes
                if len(code) == 2 and code.isalpha():
                    countries.add(code)
        
    # Convert to list of dicts and sort by code
    country_list = [{"code": code, "name": code} for code in countries]
    country_list.sort(key=lambda x: x["code"]) 
        
    return {
        "countries": country_list,
        "total": len(country_list)
    }

@router.get("/channels", response_model=dict)
async def get_channels(
    country: str = Query("CA", description="Country filter (2-letter code)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=10, le=100, description="Items per page")
):
    """Get paginated channels filtered by country (server-side).
    
    The `country` parameter expects 2-letter country codes like 'CA', 'US', 'UK', etc.
    Returns paginated results with total count and page info.
    """
    country = (country or "CA").upper()
    offset = (page - 1) * per_page
    
    async with get_session() as session:
        # Build where clause for country prefix
        where_clause = Channel.name.startswith(f"{country}|")
        order_by_clause = [Channel.channel_id.collate('NOCASE')]

        # Get total count for pagination
        count_result = await session.execute(
            select(Channel).where(where_clause)
        )
        total = len(count_result.scalars().all())
        
        # Get paginated results with program counts
        result = await session.execute(
            select(
                Channel,
                func.count(Program.id).label('program_count')
            )
            .outerjoin(Program, Channel.id == Program.channel_id)
            .where(where_clause)
            .group_by(Channel.id)
            .order_by(*order_by_clause)
            .offset(offset)
            .limit(per_page)
        )
        
        # Convert SQLAlchemy models to dictionaries
        channels = []
        for channel, program_count in result.all():
            channels.append({
                "id": channel.id,
                "name": channel.name,
                "channel_id": channel.channel_id,
                "icon_url": channel.icon_url,
                "program_count": program_count
            })
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "channels": channels
        }

@router.get("/schedule/{channel_id}", response_model=dict)
async def get_channel_schedule(channel_id: int):
    """Get the program schedule for a specific channel (all programs)."""
    async with get_session() as session:
        # First verify the channel exists and get its details
        channel_result = await session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel with id {channel_id} not found")
        
        # Convert channel to dict
        channel_dict = {
            "id": channel.id,
            "name": channel.name,
            "channel_id": channel.channel_id,
            "icon_url": channel.icon_url
        }
        
        # Get ALL programs ordered by start time
        result = await session.execute(
            select(Program)
            .where(Program.channel_id == channel_id)
            .order_by(Program.start_time)
        )
        programs = result.scalars().all()
        
        # Convert programs to dicts (emit UTC ISO8601 with 'Z')
        from datetime import timezone
        def to_utc_iso(dt):
            if not dt:
                return None
            # Data model stores UTC as naive; if naive, assume UTC (not server local)
            if dt.tzinfo is None:
                aware = dt.replace(tzinfo=timezone.utc)
            else:
                aware = dt
            dt_utc = aware.astimezone(timezone.utc)
            iso = dt_utc.isoformat()
            # Ensure Z suffix
            if iso.endswith("+00:00"):
                iso = iso[:-6] + "Z"
            return iso
        program_list = []
        for program in programs:
            program_list.append({
                "id": program.id,
                "title": program.title,
                "description": program.description,
                "start_time": to_utc_iso(program.start_time),
                "end_time": to_utc_iso(program.end_time),
                "category": program.category,
                "channel_id": program.channel_id
            })
        
        return {
            "total": len(program_list),
            "programs": program_list,
            "channel": channel_dict
        }

        # Add channel info to each program for convenience
        program_list = []
        for p in programs:
            program_list.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "start_time": p.start_time,
                "end_time": p.end_time,
                "category": p.category,
                "channel_id": p.channel_id,
            })
            
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "programs": program_list,
            "channel": channel
        }