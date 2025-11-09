"""SQLAlchemy models for the EPG database."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

class Channel(Base):
    """TV Channel model."""
    __tablename__ = "channels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    programs: Mapped[list["Program"]] = relationship(
        "Program", back_populates="channel", cascade="all, delete-orphan"
    )

class Program(Base):
    """TV Program model."""
    __tablename__ = "programs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("channels.id"), nullable=False
    )
    
    channel: Mapped[Channel] = relationship("Channel", back_populates="programs")