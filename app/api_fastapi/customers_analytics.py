from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.customers import calc_customer_tier, customer_aggregates, customer_leaderboard

router = APIRouter(prefix="/customers-analytics", tags=["customers-analytics"])

@router.get("/aggregates")
def api_customer_aggregates(db: Session = Depends(get_db)):
    return customer_aggregates(db)

@router.get("/leaderboard")
def api_customer_leaderboard(limit: int = 100, db: Session = Depends(get_db)):
    return customer_leaderboard(db, limit=limit)


