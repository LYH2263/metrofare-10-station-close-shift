from fastapi import APIRouter, HTTPException
from app.schemas.station import CloseStationRequest
from app.services.metro_service import MetroService, StationClosureError

router = APIRouter(tags=["stations"])

ERROR_STATUS = {
    "station_not_found": 404,
    "already_closed": 409,
    "not_closed": 409,
    "reroute_missing": 400,
    "reroute_closed": 400,
    "reroute_not_adjacent": 400,
}


@router.get("/stations")
def list_stations(include_closed: bool = False):
    with MetroService() as s:
        return {"items": s.stations(include_closed=include_closed)}


@router.get("/stations/{code}")
def get_station(code: str):
    with MetroService() as s:
        row = s.station(code)
        if not row:
            raise HTTPException(404)
        return row


@router.post("/stations/{code}/close")
def close_station(code: str, body: CloseStationRequest):
    with MetroService() as s:
        try:
            return s.close_station(code, body.reroute_to, body.reason)
        except StationClosureError as e:
            raise HTTPException(ERROR_STATUS.get(str(e), 400), detail=str(e))


@router.post("/stations/{code}/unclose")
def unclose_station(code: str):
    with MetroService() as s:
        try:
            return s.unclose_station(code)
        except StationClosureError as e:
            raise HTTPException(ERROR_STATUS.get(str(e), 400), detail=str(e))
