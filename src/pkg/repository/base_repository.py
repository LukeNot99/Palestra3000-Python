from contextlib import contextmanager


class BaseRepository:
    """
    Classe base per tutti i repository.
    Fornisce un costruttore standard e un context manager per la gestione delle sessioni DB.
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    @contextmanager
    def _get_session(self):
        """Context manager per gestire automaticamente apertura/chiusura sessioni DB."""
        db = self.session_factory()
        try:
            yield db
        finally:
            db.close()
