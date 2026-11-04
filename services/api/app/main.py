"""API entrypoint. Schema creation/migrations run in deployment, not on import."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.observability import access_logs
from app.modules.companies.routes import router as companies_router
from app.modules.companies.research_routes import router as research_router
from app.modules.countries.routes import router as countries_router
from app.modules.insights.routes import router as insights_router
from app.modules.sectors.routes import router as sectors_router
from app.modules.watchlists.routes import router as watchlists_router
from app.shared.database.readiness import database_ready
from app.shared.database.session import engine

app = FastAPI(title=settings.app_name)
app.middleware("http")(access_logs)
app.include_router(countries_router)
app.include_router(sectors_router)
app.include_router(companies_router)
app.include_router(research_router)
app.include_router(insights_router)
app.include_router(watchlists_router)


@app.get("/health/live")
def liveness():
    return {"status": "ok"}


@app.get("/health")
@app.get("/health/ready")
def readiness():
    if not database_ready(engine):
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unavailable_or_unmigrated"},
        )
    return {"status": "ok", "database": "up"}
