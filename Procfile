web: python -c "from app.models.base import Base; from app.database import engine; Base.metadata.create_all(engine)" && python complete_seeder.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
