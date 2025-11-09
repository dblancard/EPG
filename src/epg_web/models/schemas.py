"""Pydantic models for API request/response validation."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

class ChannelBase(BaseModel):
    """Base Channel schema."""
    name: str
    channel_id: str
    icon_url: Optional[str] = None

class ChannelCreate(ChannelBase):
    """Channel creation schema."""
    pass

class ChannelResponse(ChannelBase):
    """Channel response schema."""
    id: int
    
    class Config:
        """Pydantic model configuration."""
        from_attributes = True

class ProgramBase(BaseModel):
    """Base Program schema."""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    category: Optional[str] = None

class ProgramCreate(ProgramBase):
    """Program creation schema."""
    # XMLTV/JSON parsers supply the source channel identifier (string)
    # which will be mapped to a database integer id by the storage layer.
    channel_id: str

class ProgramResponse(ProgramBase):
    """Program response schema."""
    id: int
    channel_id: int
    # channel display name (human-friendly) included so clients can show the channel
    # without doing an extra lookup. This will be populated by the API.
    channel_name: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        from_attributes = True

class EPGData(BaseModel):
    """EPG data schema for file parsing."""
    channels: List[ChannelCreate]
    programs: List[ProgramCreate]

class EPGSourceUpdate(BaseModel):
    """Schema for updating EPG data from a URL."""
    url: HttpUrl
    description: Optional[str] = None