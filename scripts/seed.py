"""Seed the database with a handful of fake toilet locations.

Usage (from the project root):
    python -m scripts.seed
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, init_db
from app.models import Toilet

# Fake toilets clustered around central London (51.5074, -0.1278)
SEED_DATA = [
    {
        "name": "Trafalgar Square Public Toilet",
        "address": "Trafalgar Square, London WC2N 5DN",
        "latitude": 51.5080,
        "longitude": -0.1281,
        "is_accessible": True,
        "is_free": True,
        "opening_hours": "24/7",
    },
    {
        "name": "Covent Garden Market Facilities",
        "address": "The Market Building, Covent Garden, London WC2E 8RF",
        "latitude": 51.5117,
        "longitude": -0.1228,
        "is_accessible": True,
        "is_free": False,
        "opening_hours": "Mon-Sun 08:00-22:00",
    },
    {
        "name": "Leicester Square Underground",
        "address": "Leicester Square Station, London WC2H 7NA",
        "latitude": 51.5113,
        "longitude": -0.1281,
        "is_accessible": False,
        "is_free": False,
        "opening_hours": "Mon-Sat 06:00-24:00, Sun 07:00-23:30",
    },
    {
        "name": "Embankment Gardens Toilet Block",
        "address": "Victoria Embankment, London WC2N 6NS",
        "latitude": 51.5072,
        "longitude": -0.1215,
        "is_accessible": True,
        "is_free": True,
        "opening_hours": "08:00-20:00",
    },
    {
        "name": "Soho Square Public Convenience",
        "address": "Soho Square, London W1D 3QN",
        "latitude": 51.5151,
        "longitude": -0.1317,
        "is_accessible": False,
        "is_free": True,
        "opening_hours": "07:00-21:00",
    },
    {
        "name": "Waterloo Station South Entrance",
        "address": "Waterloo Station, London SE1 8SW",
        "latitude": 51.5034,
        "longitude": -0.1133,
        "is_accessible": True,
        "is_free": False,
        "opening_hours": "05:00-01:00",
    },
    {
        "name": "St James's Park Facilities",
        "address": "St James's Park, London SW1A 2BJ",
        "latitude": 51.5023,
        "longitude": -0.1337,
        "is_accessible": True,
        "is_free": True,
        "opening_hours": "08:00-dusk",
    },
    {
        "name": "Oxford Street (east) Public Toilet",
        "address": "Oxford Street, London W1C 1JN",
        "latitude": 51.5154,
        "longitude": -0.1410,
        "is_accessible": True,
        "is_free": False,
        "opening_hours": "09:00-21:00",
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Toilet).count()
        if existing:
            print(f"Database already has {existing} toilet(s). Skipping seed.")
            return

        for data in SEED_DATA:
            toilet = Toilet(
                **data,
                location=f"SRID=4326;POINT({data['longitude']} {data['latitude']})",
            )
            db.add(toilet)

        db.commit()
        print(f"Seeded {len(SEED_DATA)} toilets.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
