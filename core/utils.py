from datetime import datetime
import re
import os
import webbrowser

def parse_date(date_str):
    if not date_str: return None
    date_str = date_str.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try: return datetime.strptime(date_str, fmt)
        except ValueError: continue
    return None

def is_valid_date(date_str):
    if not date_str or not date_str.strip(): return True 
    return parse_date(date_str) is not None

def estrai_consonanti(testo):
    return re.sub(r'[^A-Z]', '', re.sub(r'[AEIOU]', '', testo.upper()))

def estrai_vocali(testo):
    return re.sub(r'[^AEIOU]', '', testo.upper())

def calcola_cf_parziale(nome, cognome, data_nascita_str, sesso):
    """Calcola i primi 11 caratteri esatti del CF, lascia le X per il comune."""
    if not nome or not cognome or not data_nascita_str:
        return ""
        
    dt = parse_date(data_nascita_str)
    if not dt: return ""

    # COGNOME
    cog_c = estrai_consonanti(cognome)
    cog_v = estrai_vocali(cognome)
    cf_cognome = (cog_c + cog_v + "XXX")[:3]

    # NOME
    nom_c = estrai_consonanti(nome)
    nom_v = estrai_vocali(nome)
    if len(nom_c) >= 4:
        cf_nome = nom_c[0] + nom_c[2] + nom_c[3]
    else:
        cf_nome = (nom_c + nom_v + "XXX")[:3]

    # ANNO e MESE
    anno = str(dt.year)[-2:]
    mesi_cf = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'H', 7:'L', 8:'M', 9:'P', 10:'R', 11:'S', 12:'T'}
    mese = mesi_cf[dt.month]

    # GIORNO / SESSO
    giorno = dt.day
    if sesso.upper() == 'F':
        giorno += 40
    giorno_str = f"{giorno:02d}"

    cf_parziale = f"{cf_cognome}{cf_nome}{anno}{mese}{giorno_str}XXXX"
    return cf_parziale

def genera_fattura_html(socio):
    """Genera una ricevuta in HTML (2 copie per foglio A4) e la apre nel browser."""
    cartella_fatture = os.path.join(os.getcwd(), "Ricevute")
    os.makedirs(cartella_fatture, exist_ok=True)
    
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    orario = datetime.now().strftime("%H%M%S")
    
    nome_file = f"Ricevuta_{socio.last_name}_{socio.first_name}_{orario}.html"
    percorso_file = os.path.join(cartella_fatture, nome_file)
    
    cf_print = socio.codice_fiscale if socio.codice_fiscale else "_________________________"
    indirizzo_print = socio.address if socio.address else "____________________________________"
    
    def blocco_ricevuta(tipo_copia):
        return f"""
        <div class="invoice-box">
            <div class="copia-label">{tipo_copia}</div>
            <div class="header">
                <div class="header-left">
                    <h1>RICEVUTA</h1>
                    <p style="margin-top: 15px; font-size: 16px;">
                        Data: <strong>{data_oggi}</strong><br><br>
                        Numero: ___________________
                    </p>
                </div>
                <div class="header-right">
                    <div class="timbro-box">
                        Spazio Timbro
                    </div>
                </div>
            </div>
            
            <div class="details">
                <h3 style="margin: 0 0 10px 0; color: #2C2C2E; font-size: 18px;">Intestato a:</h3>
                <p style="margin: 0; font-size: 16px; line-height: 1.6;">
                    <strong>{socio.first_name} {socio.last_name}</strong><br>
                    Codice Fiscale: <strong>{cf_print}</strong><br>
                    Indirizzo: {indirizzo_print}
                </p>
            </div>
            
            <table class="item-table">
                <thead>
                    <tr>
                        <th>Descrizione</th>
                        <th style="text-align: right; width: 200px;">Importo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 20px 10px; font-size: 16px;">Quota partecipazione corso attività sportiva dilettantistica</td>
                        <td style="text-align: right; font-weight: bold; font-size: 22px;">€ ____________</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="footer-grid">
                <div></div>
                <div class="signature">
                    <div class="signature-line"></div>
                    <div style="font-size: 14px; text-align: right;">Firma</div>
                </div>
            </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Ricevuta {socio.last_name}</title>
        <style>
            /* Impostazioni per la stampa in A4 */
            @page {{ size: A4 portrait; margin: 0; }}
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #555; box-sizing: border-box; }}
            
            /* Il foglio A4 virtuale */
            .page {{ width: 210mm; height: 296mm; margin: auto; background: white; padding: 15mm; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 0 10px rgba(0,0,0,0.5); }}
            
            .invoice-box {{ height: 46%; position: relative; display: flex; flex-direction: column; }}
            
            .copia-label {{ font-size: 11px; color: #888; text-align: right; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }}
            
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #007AFF; padding-bottom: 15px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: #007AFF; font-size: 32px; letter-spacing: 1px; }}
            
            .header-left {{ display: flex; flex-direction: column; justify-content: space-between; }}
            .header-right {{ display: flex; align-items: flex-start; }}
            
            /* Il box del timbro in alto a destra */
            .timbro-box {{ width: 180px; height: 110px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; color: #bbb; font-size: 12px; }}
            
            .details {{ margin-bottom: 30px; }}
            
            .item-table {{ width: 100%; border-collapse: collapse; margin-bottom: auto; }}
            .item-table th, .item-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            .item-table th {{ background-color: #f2f2f7; color: #1D1D1F; font-size: 14px; text-transform: uppercase; }}
            
            .footer-grid {{ display: flex; justify-content: space-between; align-items: flex-end; margin-top: 30px; }}
            
            /* Spazio per la firma in basso a destra */
            .signature {{ width: 250px; }}
            .signature-line {{ border-bottom: 1px solid #333; margin-bottom: 8px; height: 40px; }}
            
            /* Linea di taglio tratteggiata tra le due ricevute */
            .cut-line {{ text-align: center; border-bottom: 2px dashed #ccc; margin: 0; line-height: 0.1em; color: #ccc; }}
            .cut-line span {{ background: white; padding: 0 15px; font-size: 20px; }}
            
            @media print {{ 
                body {{ background-color: white; padding: 0; }} 
                .page {{ box-shadow: none; margin: 0; width: 100%; height: 100%; }}
            }}
        </style>
    </head>
    <body>
        <div class="page">
            {blocco_ricevuta("Copia per il Cliente")}
            <div class="cut-line"><span>&#9986;</span></div>
            {blocco_ricevuta("Copia per l'Associazione")}
        </div>
    </body>
    </html>
    """
    
    with open(percorso_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    webbrowser.open(f"file://{percorso_file}")