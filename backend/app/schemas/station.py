from pydantic import BaseModel


class CloseStationRequest(BaseModel):
    reroute_to: str | None = None
    reason: str = ""
