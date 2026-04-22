from .base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Member(Base):
    __tablename__ = "members"
    city = Column(String, nullable=True)
    gender = Column(String, default="M")
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    birth_place = Column(String, nullable=True)
    codice_fiscale = Column(String, nullable=True)
    other_contact = Column(String, nullable=True) 
    id = Column(Integer, primary_key=True, index=True)
    badge_number = Column(String, unique=True, index=True, nullable=True)
    
    entries_used = Column(Integer, default=0)
    membership_start = Column(String, nullable=True) 
    membership_expiration = Column(String, nullable=True)
    enrollment_expiration = Column(String, nullable=True) 
    certificate_expiration = Column(String, nullable=True)
    has_medical_certificate = Column(Boolean, default=False)
    tier_id = Column(Integer, ForeignKey("tiers.id"), nullable=True)
    tier = relationship("Tier")
