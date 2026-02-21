from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ToiletCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = None
    address: str | None = Field(default=None, max_length=400)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_accessible: bool | None = None
    is_free: bool | None = None
    opening_hours: str | None = Field(default=None, max_length=200)


class ToiletResponse(BaseModel):
    id: int
    name: str
    description: str | None
    address: str | None
    latitude: float
    longitude: float
    is_accessible: bool | None
    is_free: bool | None
    opening_hours: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NearbyToilet(ToiletResponse):
    """ToiletResponse extended with the distance from the search point."""

    distance_meters: float


class NearbySearchParams(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius: float = Field(default=500, gt=0, le=50_000, description="Search radius in metres")
    limit: int = Field(default=20, gt=0, le=100)
