from app.models import Company


def generate_mock_insight(company: Company) -> dict:
    return {
        "summary": f"{company.name} operates in {company.sector.name} with a fundamentally focused profile.",
        "business_model": company.description or f"{company.name} generates value through core operations in its industry.",
        "quality_view": "Quality appears supported by recurring revenue potential and operating discipline.",
        "growth_view": "Growth should be evaluated through revenue, margin, and free cash flow trends.",
        "valuation_view": "Valuation should be compared against peers and historical multiples.",
        "balance_sheet_view": "Balance sheet strength depends on debt levels, liquidity, and equity coverage.",
        "risk_view": "Key risks include macro sensitivity, sector cycles, and execution risk.",
        "opportunities": ["Operational efficiency", "Sector demand tailwinds"],
        "risks": ["Macro volatility", "Valuation compression"],
        "questions_for_further_research": [
            "How sustainable are margins over a full cycle?",
            "Is free cash flow conversion stable?",
        ],
        "disclaimer": "This is investment research support, not financial advice.",
    }
