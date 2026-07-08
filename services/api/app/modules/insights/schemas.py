from pydantic import BaseModel


class AIInsightOut(BaseModel):
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
