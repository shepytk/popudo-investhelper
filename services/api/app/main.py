from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.modules.companies.routes import router as companies_router
from app.modules.countries.routes import router as countries_router
from app.modules.insights.routes import router as insights_router
from app.modules.sectors.routes import router as sectors_router
from app.shared.database.base import Base
from app.shared.database.session import SessionLocal, engine
from scripts.seed_sample_companies import seed_data


Base.metadata.create_all(bind=engine)
with SessionLocal() as session:
    seed_data(session)

app = FastAPI(title=settings.app_name)

app.include_router(countries_router)
app.include_router(sectors_router)
app.include_router(companies_router)
app.include_router(insights_router)


@app.get("/health")
def health():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {"status": "ok" if db_ok else "degraded", "database": "up" if db_ok else "down"}
