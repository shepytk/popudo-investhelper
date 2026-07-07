from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    id: int
    name: str
    iso_code: str
    currency_code: str
    region: str

    model_config = ConfigDict(from_attributes=True)
