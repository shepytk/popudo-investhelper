from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

kwargs = {"pool_pre_ping": True, "future": True}
if not settings.database_url.startswith("sqlite"):
    kwargs.update({"pool_size": 5, "max_overflow": 10, "pool_recycle": 1800})
engine = create_engine(settings.database_url, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    with SessionLocal() as db:
        yield db
