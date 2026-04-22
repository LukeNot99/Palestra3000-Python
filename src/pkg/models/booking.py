from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    member = relationship("Member")
    lesson = relationship("Lesson")
