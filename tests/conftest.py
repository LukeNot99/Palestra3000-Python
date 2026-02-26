import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base

# Creiamo un database temporaneo in RAM per i test
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """
    Questa 'fixture' viene chiamata prima di OGNI singolo test.
    Crea un database vuoto, fornisce la sessione, e alla fine distrugge tutto.
    """
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session  # Passa la sessione al test
    
    # Pulizia finale dopo il test
    session.close()
    Base.metadata.drop_all(bind=engine)