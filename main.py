from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import init_database, get_db
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")
    init_database()
    yield

app = FastAPI(
    title="Reinsurance Processing API",
    description="API for processing reinsurance documents and data",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Reinsurance Processing API is running"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}

