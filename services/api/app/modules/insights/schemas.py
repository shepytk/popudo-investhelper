from pydantic import BaseModel, ConfigDict


class EvidenceOut(BaseModel):
    metric_period: str
    published_date: str
    retrieved_at: str
    source: str
    source_url: str
    reporting_currency: str
    amount_unit: str


class AIInsightOut(BaseModel):
    status: str
    as_of: str
    evidence: list[EvidenceOut]
    summary: str
    business_model: str
    quality_view: str
    growth_view: str
    valuation_view: str
    balance_sheet_view: str
    risk_view: str
    opportunities: list[str]
    risks: list[str]
    questions_for_further_research: list[str]
    disclaimer: str

    model_config = ConfigDict(extra="forbid")
