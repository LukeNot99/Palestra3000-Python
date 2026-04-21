from sqlalchemy import Column, Integer, String, Boolean
from core.database import Base

class DashboardConfig(Base):
    __tablename__ = "dashboard_config"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
