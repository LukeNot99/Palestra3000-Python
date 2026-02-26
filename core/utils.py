from datetime import datetime

def parse_date(date_str):
    """
    Tenta di convertire una stringa in un oggetto datetime.
    Supporta automaticamente i formati GG/MM/AAAA e AAAA-MM-GG.
    Ritorna None se la data è vuota o invalida.
    """
    if not date_str: 
        return None
    
    date_str = date_str.strip()
    
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    return None

def is_valid_date(date_str):
    """
    Verifica se una stringa è una data valida per il gestionale.
    Se la stringa è vuota ritorna True (poiché molti campi data sono opzionali).
    """
    if not date_str or not date_str.strip(): 
        return True 
    return parse_date(date_str) is not None