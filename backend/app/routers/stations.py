from fastapi import APIRouter, HTTPException
from app.schemas.station import CloseRequest
from app.services.metro_service import MetroService

router = APIRouter(tags=["stations"])


@router.get("/stations")
def list_stations(include_closed: bool = False):
    with MetroService() as s:
        return {"items": s.stations(include_closed)}


@router.get("/stations/{code}")
def get_station(code: str):
    with MetroService() as s:
        row = s.station(code)
        if not row:
            raise HTTPException(404)
        return row


@router.post("/stations/{code}/close")
def close_station(code: str, body: CloseRequest):
    with MetroService() as s:
        try:
            return s.close_station(code, body.divert_to, body.reason)
        except ValueError as e:
            raise HTTPException(400, str(e))


@router.post("/stations/{code}/unclose")
def unclose_station(code: str):
    with MetroService() as s:
        try:
            return s.unclose_station(code)
        except ValueError as e:
            raise HTTPException(400, str(e))
