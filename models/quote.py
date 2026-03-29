"""
Quote model — Islamic quotes for prayer reminders.
"""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="hadith")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    surah_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    surah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ayah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prayer_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Quote(id={self.id}, type={self.type})>"
