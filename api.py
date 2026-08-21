import models
import schemas

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends

from database import SessionLocal, engine
from typing import List
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SharkBait API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.mount("/static", StaticFiles(directory="static"), name="static")

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
