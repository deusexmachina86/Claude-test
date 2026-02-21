from datetime import datetime, timezone

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Toilet(Base):
    __tablename__ = "toilets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(400), nullable=True)

    # PostGIS geography column — POINT(lng lat), SRID 4326 (WGS84)
    # Geography type automatically uses meters for distance calculations
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )

    # Denormalised lat/lng for cheap reads without geometry parsing
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    is_accessible: Mapped[bool | None] = mapped_column(nullable=True)
    is_free: Mapped[bool | None] = mapped_column(nullable=True)
    opening_hours: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
