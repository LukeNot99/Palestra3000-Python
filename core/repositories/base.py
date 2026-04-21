"""Base repository with generic CRUD operations and session management."""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from core.database import SessionLocal

T = TypeVar('T')


def get_db() -> Session:
    """Factory function per ottenere una nuova sessione database."""
    return SessionLocal()


class BaseRepository(Generic[T]):
    """Classe base generica per tutti i repository."""
    
    def __init__(self, db: Session, model_class: Type[T]):
        """Inizializza il repository con una sessione database e la classe modello."""
        self.db = db
        self.model_class = model_class
    
    def get_all(self) -> List[T]:
        """Ottiene tutti gli elementi."""
        return self.db.query(self.model_class).all()
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Ottiene un elemento per ID."""
        return self.db.get(self.model_class, entity_id)
    
    def save(self, entity: T) -> T:
        """Salva un'entità (insert o update)."""
        if hasattr(entity, 'id') and entity.id:
            existing = self.get_by_id(entity.id)
            if existing:
                for key, value in entity.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                entity = existing
            else:
                self.db.add(entity)
        else:
            self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Elimina un elemento per ID."""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Conta il numero totale di elementi."""
        return self.db.query(self.model_class).count()
