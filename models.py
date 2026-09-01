from database import Base
from sqlalchemy import Column, Float, Integer, String

class Deal(Base):
    __tablename__= "deals"

    id = Column(Integer, primary_key=True, index=True)
    dealID = Column(String, unique=True, index=True, nullable=False)

    title = Column(String, index=True, nullable=False)
    shop = Column(String, nullable=False)
    price_now = Column(Float, nullable=False, index=True)
    normal_price = Column(Float, nullable=False)
    metacritic = Column(Float, nullable=True)
    steam_rate = Column(String, nullable=True)
    steam_rate_percent = Column(Float, nullable=True)
    critic_steam = Column(Float, nullable=False)
    sort_rate_price = Column(Float, nullable=False, index=True)
    thumb = Column(String, nullable=True)