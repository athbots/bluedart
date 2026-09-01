"""
Routes API Endpoints.
Provides route directory, route details, and train-style route progression.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from services.api.app.core.database import get_db
from services.api.app.core.live_state import live_state
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop
from services.api.app.services.progression_service import ProgressionService
from packages.schemas.transit import RouteBase, RouteDetail, RouteDirectionBase, RouteStopBase, StopBase, RouteProgressionView

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("", response_model=List[RouteBase])
def get_routes(
    active_only: bool = Query(True),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List transit routes.
    """
    query = db.query(Route)
    if active_only:
        query = query.filter(Route.active == True)
    if city:
        query = query.filter(Route.city == city)
    routes = query.all()

    results = []
    for r in routes:
        dirs = [
            RouteDirectionBase(
                id=d.id,
                route_id=d.route_id,
                direction=d.direction,
                origin=d.origin,
                destination=d.destination,
            )
            for d in r.directions
        ]
        results.append(
            RouteBase(
                id=r.id,
                route_number=r.route_number,
                name=r.name,
                origin=r.origin,
                destination=r.destination,
                city=r.city,
                active=r.active,
                directions=dirs,
            )
        )
    return results


@router.get("/{route_id}", response_model=RouteDetail)
def get_route_detail(route_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full route details with ordered stops per direction.
    """
    r = db.query(Route).filter(Route.id == route_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

    dirs = [
        RouteDirectionBase(
            id=d.id,
            route_id=d.route_id,
            direction=d.direction,
            origin=d.origin,
            destination=d.destination,
        )
        for d in r.directions
    ]

    # Get stops for primary outbound direction
    stops: List[RouteStopBase] = []
    if r.directions:
        outbound = r.directions[0]
        r_stops = (
            db.query(RouteStop, Stop)
            .join(Stop, RouteStop.stop_id == Stop.id)
            .filter(RouteStop.route_direction_id == outbound.id)
            .order_by(RouteStop.sequence.asc())
            .all()
        )
        for rs, s in r_stops:
            stops.append(
                RouteStopBase(
                    id=rs.id,
                    route_direction_id=rs.route_direction_id,
                    stop_id=rs.stop_id,
                    sequence=rs.sequence,
                    scheduled_offset_seconds=rs.scheduled_offset_seconds,
                    cumulative_distance_meters=rs.cumulative_distance_meters,
                    stop=StopBase(
                        id=s.id,
                        name=s.name,
                        city=s.city,
                        state=s.state,
                        latitude=s.latitude,
                        longitude=s.longitude,
                        is_major_stop=s.is_major_stop,
                        is_intercity_stop=s.is_intercity_stop,
                        address=s.address,
                    ),
                )
            )

    return RouteDetail(
        id=r.id,
        route_number=r.route_number,
        name=r.name,
        origin=r.origin,
        destination=r.destination,
        city=r.city,
        active=r.active,
        directions=dirs,
        stops=stops,
    )


@router.get("/{route_id}/progress", response_model=RouteProgressionView)
def get_route_progression(
    route_id: str,
    vehicle_id: str = Query(..., description="ID of the active vehicle on this route"),
    user_stop_id: Optional[str] = Query(None, description="Optional commuter stop ID to highlight"),
    db: Session = Depends(get_db),
):
    """
    Train-style linear route progression visualization.
    Shows the bus's relative position across the ordered stops sequence,
    highlighting past stops, current segment, and the commuter's selected stop.
    """
    v_state = live_state.get_vehicle_state(vehicle_id)
    if not v_state:
        raise HTTPException(status_code=404, detail=f"Active vehicle '{vehicle_id}' not found in live fleet")

    view = ProgressionService.get_route_progression_view(
        db=db,
        vehicle_id=vehicle_id,
        live_bus=v_state,
        user_stop_id=user_stop_id,
    )
    if not view:
        raise HTTPException(status_code=404, detail="Could not derive progression for vehicle/route")
    return view
