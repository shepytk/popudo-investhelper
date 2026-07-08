from pydantic import BaseModel, ConfigDict


class SectorOut(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class SectorCompanyOut(BaseModel):
    id: int
    name: str
    ticker: str


class SectorWithCompaniesOut(SectorOut):
    companies: list[SectorCompanyOut]
