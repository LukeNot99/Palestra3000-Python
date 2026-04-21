from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    badge_number = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    codice_fiscale = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    birth_place = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    other_contact = Column(String, nullable=True) 
    gender = Column(String, default="M")
    
    enrollment_expiration = Column(String, nullable=True) 
    membership_start = Column(String, nullable=True) 
    membership_expiration = Column(String, nullable=True)
    has_medical_certificate = Column(Boolean, default=False)
    certificate_expiration = Column(String, nullable=True)
    entries_used = Column(Integer, default=0)
    tier_id = Column(Integer, ForeignKey("tiers.id"), nullable=True)
    tier = relationship("Tier")
