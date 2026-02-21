from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Toilet
from app.schemas import NearbyToilet, ToiletCreate, ToiletResponse

router = APIRouter(prefix="/toilets", tags=["toilets"])


def _make_point(lat: float, lng: float) -> str:
    """Return a WKT geography point string for PostGIS."""
    return f"SRID=4326;POINT({lng} {lat})"


@router.post("/", response_model=ToiletResponse, status_code=201)
def create_toilet(payload: ToiletCreate, db: Session = Depends(get_db)):
    toilet = Toilet(
        name=payload.name,
        description=payload.description,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location=_make_point(payload.latitude, payload.longitude),
        is_accessible=payload.is_accessible,
        is_free=payload.is_free,
        opening_hours=payload.opening_hours,
    )
    db.add(toilet)
    db.commit()
    db.refresh(toilet)
    return toilet


@router.get("/nearby", response_model=list[NearbyToilet])
def get_nearby_toilets(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=500, gt=0, le=50_000, description="Radius in metres"),
    limit: int = Query(default=20, gt=0, le=100),
    db: Session = Depends(get_db),
):
    search_point = ST_GeogFromText(f"POINT({lng} {lat})")

    rows = db.execute(
        select(
            Toilet,
            ST_Distance(Toilet.location, search_point).label("distance_meters"),
        )
        .where(ST_DWithin(Toilet.location, search_point, radius))
        .order_by("distance_meters")
        .limit(limit)
    ).all()

    results = []
    for toilet, distance in rows:
        data = ToiletResponse.model_validate(toilet).model_dump()
        data["distance_meters"] = round(distance, 2)
        results.append(NearbyToilet(**data))
    return results


@router.get("/{toilet_id}", response_model=ToiletResponse)
def get_toilet(toilet_id: int, db: Session = Depends(get_db)):
    toilet = db.get(Toilet, toilet_id)
    if toilet is None:
        raise HTTPException(status_code=404, detail="Toilet not found")
    return toilet
