from datetime import date

from pydantic import BaseModel, ConfigDict


class ListingOut(BaseModel):
    id: int
    security_id: int
    mic: str
    symbol: str
    currency_code: str
    is_adr: bool
    valid_from: date
    valid_to: date | None
    verified: bool

    model_config = ConfigDict(from_attributes=True)
