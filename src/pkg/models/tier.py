from sqlalchemy import Column, Integer, String, Float
from .base import Base

class Tier(Base):
    __tablename__ = "tiers"
    cost = Column(Float, default=0.0)
    min_age = Column(Integer, default=0)
    max_age = Column(Integer, default=999)
    max_entries = Column(Integer, default=0) 
    end_time = Column(String, default="23:59")
    start_time = Column(String, default="00:00")
    duration_months = Column(Integer, default=1) 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
