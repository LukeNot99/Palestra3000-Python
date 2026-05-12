import sqlite3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importa i tuoi modelli
from src.pkg.models.base import Base
from src.pkg.models.member import Member
from src.pkg.models.activity import Activity
from src.pkg.models.tier import Tier

# Percorsi dei database
OLD_DB_PATH = 'Archivio Palestra.sqlite'
NEW_DB_URL = 'sqlite:///src/data/palestra3000.db'

def main():
    if not os.path.exists(OLD_DB_PATH):
        print(f"ERRORE: Non trovo il file {OLD_DB_PATH}. Assicurati che sia nella stessa cartella dello script.")
        return

    # Connessione al vecchio DB
    old_conn = sqlite3.connect(OLD_DB_PATH)
    old_conn.row_factory = sqlite3.Row 
    cursor = old_conn.cursor()

    # Connessione al nuovo DB
    engine = create_engine(NEW_DB_URL)
    Base.metadata.create_all(bind=engine) # Assicura che le tabelle esistano
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # 1. MIGRAZIONE ATTIVITa
    print("Migrazione Attività in corso...")
    cursor.execute('SELECT "ID Attivita", "Descrizione" FROM "Attività"')
    attivita_rows = cursor.fetchall()
    
    for r in attivita_rows:
        nuova_attivita = Activity(
            id=r["ID Attivita"],
            name=r["Descrizione"] if r["Descrizione"] else "Attività Senza Nome"
        )
        db.merge(nuova_attivita)
    db.commit()
    print(f" -> {len(attivita_rows)} attività migrate con successo!\n")

    # 2. MIGRAZIONE TARIFFE (QuoteAssociative)
    print("Migrazione Tariffe (QuoteAssociative) in corso...")
    cursor.execute('SELECT * FROM "QuoteAssociative"')
    tariffe_rows = cursor.fetchall()
    
    for r in tariffe_rows:
        nuova_tariffa = Tier(
            id=r["IDIscrizione"],
            name=r["Descrizione"] if r["Descrizione"] else f"Tariffa {r['IDIscrizione']}",
            cost=float(r["Costo(Euro)"] or 0),
            duration_months=int(r["Durata(Mesi)"] or 1),
            min_age=int(r["EtaMinima"] or 0),
            max_age=int(r["EtaMassima"] or 999)
        )
        db.merge(nuova_tariffa)
    db.commit()
    print(f" -> {len(tariffe_rows)} tariffe migrate con successo!\n")

    # 3. MIGRAZIONE SOCI
    print("Migrazione Soci in corso...")
    cursor.execute('SELECT * FROM "Soci"')
    soci_rows = cursor.fetchall()
    
    for r in soci_rows:
        # Unisco telefono e cellulare. Se sono vuoti, lascio None
        tel_cell = f"{r['Telefono'] or ''} {r['Cellulare'] or ''}".strip()
        telefono_finale = tel_cell if tel_cell else None
        
        # Gestione del badge: se è 0 lo lascio vuoto (None) per non violare l'unicità
        badge = str(r["NumeroScheda"]) if r["NumeroScheda"] and r["NumeroScheda"] != 0 else None
        
        nuovo_socio = Member(
            id=r["IDSocio"],
            first_name=r["Nome"] or "Sconosciuto",
            last_name=r["Cognome"] or "Sconosciuto",
            city=r["Comune di Residenza"],
            gender="M" if r["SessoMaschile"] == 1 else "F",
            phone=telefono_finale,
            address=r["Indirizzo"],
            birth_date=str(r["Data di Nascita"]) if r["Data di Nascita"] else None,
            birth_place=r["Luogo di Nascita"],
            other_contact=r["Fax"], # Uso other_contact per eventuale Fax
            badge_number=badge,
            has_medical_certificate=bool(r["CertificatoMedico"]),
            certificate_expiration=str(r["ScadenzaCM"]) if r["ScadenzaCM"] else None,
            membership_start=str(r["Data Iscrizione"]) if r["Data Iscrizione"] else None,
            enrollment_expiration=str(r["Scadenza Iscrizione"]) if r["Scadenza Iscrizione"] else None,
            membership_expiration=str(r["Scadenza Mensilità"]) if r["Scadenza Mensilità"] else None,
            tier_id=r["IDFascia"] if r["IDFascia"] else None
        )
        db.merge(nuovo_socio)
        
    db.commit()
    print(f" -> {len(soci_rows)} soci migrati con successo!\n")

    # Pulizia
    old_conn.close()
    db.close()
    print("MIGRAZIONE COMPLETATA CON SUCCESSO! Puoi ora avviare il nuovo programma.")

if __name__ == "__main__":
    main()