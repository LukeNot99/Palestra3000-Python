from .base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, ForeignKey

class Booking(Base):
    __tablename__ = "bookings"
    member = relationship("Member")
    lesson = relationship("Lesson")
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
