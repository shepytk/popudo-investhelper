from datetime import date
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Insight
from app.modules.insights.schemas import AIInsightOut
from app.modules.insights.service import generate_mock_insight
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/ai/companies", tags=["ai-insights"])


@router.post("/{company_id}/generate-insight", response_model=AIInsightOut)
def generate_insight(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    payload = generate_mock_insight(company)

    db.add(
        Insight(
            company_id=company_id,
            date=date.today(),
            quality_score=75,
            growth_score=72,
            valuation_score=66,
            balance_sheet_score=70,
            risk_score=45,
            overall_score=69,
            summary=payload["summary"],
            thesis=payload["quality_view"],
            risks=json.dumps(payload["risks"]),
            opportunities=json.dumps(payload["opportunities"]),
        )
    )
    db.commit()

    return payload


@router.get("/{company_id}/insights", response_model=list[AIInsightOut])
def list_insights(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    insights = list(db.scalars(select(Insight).where(Insight.company_id == company_id).order_by(Insight.created_at.desc())))
    return [
        {
            "summary": i.summary,
            "business_model": company.description,
            "quality_view": i.thesis,
            "growth_view": "Growth should be validated with statement trends.",
            "valuation_view": "Valuation should be benchmarked to peers.",
            "balance_sheet_view": "Monitor leverage and liquidity.",
            "risk_view": "Review risk flags and operating environment.",
            "opportunities": json.loads(i.opportunities),
            "risks": json.loads(i.risks),
            "questions_for_further_research": ["What drives margin durability?", "How resilient is demand?"],
            "disclaimer": "This is investment research support, not financial advice.",
        }
        for i in insights
    ]
