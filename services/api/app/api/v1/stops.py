"""
Stops API Endpoints.
Provides nearest stop discovery, stop detail, and stop-centric arrival liveboard.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from services.api.app.core.database import get_db
from services.api.app.services.geo_service import GeoService
from services.api.app.services.crowd_service import CrowdService
from packages.schemas.transit import StopWithDistance, StopBase, StopArrivalBoard

router = APIRouter(prefix="/stops", tags=["Stops"])


@router.get("/nearby", response_model=List[StopWithDistance])
def get_nearby_stops(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Commuter current latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Commuter current longitude"),
    radius_meters: float = Query(5000.0, ge=100.0, le=50000.0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Find nearest bus stops within radius from commuter's coordinates, sorted by distance.
    """
    return GeoService.get_nearby_stops(db, lat=lat, lon=lon, radius_meters=radius_meters, limit=limit)


@router.get("/{stop_id}", response_model=StopBase)
def get_stop_detail(stop_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single stop metadata.
    """
    stop = GeoService.get_stop_by_id(db, stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail=f"Stop with ID '{stop_id}' not found")
    return stop


@router.get("/{stop_id}/arrivals", response_model=StopArrivalBoard)
def get_stop_arrivals(stop_id: str, db: Session = Depends(get_db)):
    """
    Smart Bus Stop Liveboard:
    Returns all active buses approaching this stop with ETA, live/predicted crowd levels,
    and commuter decision labels (Fastest / Most Comfortable).
    """
    liveboard = CrowdService.get_stop_liveboard(db, stop_id)
    if not liveboard:
        raise HTTPException(status_code=404, detail=f"Stop with ID '{stop_id}' not found")
    return liveboard
