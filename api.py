import models
import schemas

from fastapi import FastAPI, Depends
from database import SessionLocal
from typing import List
from sqlalchemy.orm import Session


app = FastAPI(title="SharkBait API")

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/deals", response_model=List[schemas.DealResponse])
def get_deals(db: Session = Depends(get_database)):
    deals = db.query(models.Deal).order_by(models.Deal.sort_rate_price.desc()).all()
    return deals
