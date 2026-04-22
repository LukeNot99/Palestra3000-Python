from .base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey

class Lesson(Base):
    __tablename__ = "lessons"
    activity = relationship("Activity")
    date = Column(String, nullable=False)
    total_seats = Column(Integer, default=0)
    end_time = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
