from pydantic import BaseModel


class CloseRequest(BaseModel):
    divert_to: str
    reason: str = ""
